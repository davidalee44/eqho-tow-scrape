import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { mapApifyResult } from "../shared/map-apify-result.ts";

// Note: Shared imports in Deno Edge Functions use relative paths
// The shared folder needs to be accessible from each function

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

const BATCH_SIZE = 100; // Process companies in batches

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { run_id, dataset_id } = await req.json();

    if (!run_id || !dataset_id) {
      return new Response(
        JSON.stringify({ error: "Missing run_id or dataset_id" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Get Supabase client
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get Apify token
    const apifyToken = Deno.env.get("APIFY_TOKEN");
    if (!apifyToken) {
      throw new Error("APIFY_TOKEN not set");
    }

    // Update processing status
    await supabase
      .from("apify_runs")
      .update({
        processing_status: "processing",
        updated_at: new Date().toISOString(),
      })
      .eq("run_id", run_id);

    // Fetch data from Apify
    console.log(`Fetching data from Apify dataset ${dataset_id}...`);
    const apifyResponse = await fetch(
      `https://api.apify.com/v2/datasets/${dataset_id}/items?token=${apifyToken}&limit=10000`
    );

    if (!apifyResponse.ok) {
      throw new Error(
        `Apify API error: ${apifyResponse.status} ${apifyResponse.statusText}`
      );
    }

    const items = await apifyResponse.json();
    console.log(`Fetched ${items.length} items from Apify`);

    // Get run metadata to determine zone_id
    const { data: runData } = await supabase
      .from("apify_runs")
      .select("zone_id")
      .eq("run_id", run_id)
      .single();

    const zoneId = runData?.zone_id;

    if (!zoneId) {
      console.warn(`No zone_id found for run ${run_id}, skipping import`);
      await supabase
        .from("apify_runs")
        .update({
          processing_status: "failed",
          error_message: "No zone_id configured for this run",
          updated_at: new Date().toISOString(),
        })
        .eq("run_id", run_id);

      return new Response(
        JSON.stringify({
          error: "No zone_id configured for this run",
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Map and filter valid companies
    const companies: any[] = [];
    for (const item of items) {
      const mapped = mapApifyResult(item);
      if (mapped) {
        companies.push({
          ...mapped,
          zone_id: zoneId,
          scraping_stage: "google_maps",
        });
      }
    }

    console.log(`Mapped ${companies.length} valid companies from ${items.length} items`);

    // Process in batches
    let imported = 0;
    let updated = 0;
    let errors = 0;

    for (let i = 0; i < companies.length; i += BATCH_SIZE) {
      const batch = companies.slice(i, i + BATCH_SIZE);
      
      try {
        // Check for existing companies first to get accurate counts
        const googleUrls = batch.map((c) => c.google_business_url).filter(Boolean);
        const { data: existing } = await supabase
          .from("companies")
          .select("google_business_url")
          .in("google_business_url", googleUrls);

        const existingUrls = new Set(
          (existing || []).map((c) => c.google_business_url)
        );

        // Use upsert on google_business_url
        const { data, error } = await supabase
          .from("companies")
          .upsert(batch, {
            onConflict: "google_business_url",
            ignoreDuplicates: false,
          })
          .select();

        if (error) {
          console.error(`Error upserting batch ${i / BATCH_SIZE + 1}:`, error);
          errors += batch.length;
        } else {
          // Count new vs updated
          const newCount = batch.filter(
            (c) => !existingUrls.has(c.google_business_url)
          ).length;
          imported += newCount;
          updated += batch.length - newCount;
        }
      } catch (batchError) {
        console.error(`Exception processing batch ${i / BATCH_SIZE + 1}:`, batchError);
        errors += batch.length;
      }
    }

    // Update processing status
    const now = new Date().toISOString();
    await supabase
      .from("apify_runs")
      .update({
        processing_status: errors > 0 && imported === 0 ? "failed" : "completed",
        processed_at: now,
        error_message:
          errors > 0
            ? `Processed ${imported} companies, ${errors} errors`
            : null,
        updated_at: now,
      })
      .eq("run_id", run_id);

    console.log(
      `Processing complete: ${imported} imported, ${updated} updated, ${errors} errors`
    );

    return new Response(
      JSON.stringify({
        success: true,
        run_id,
        imported,
        updated,
        errors,
        total: companies.length,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Process Apify data error:", error);

    // Update run status to failed
    try {
      const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
      const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
      const supabase = createClient(supabaseUrl, supabaseServiceKey);

      const { run_id } = await req.json().catch(() => ({}));
      if (run_id) {
        await supabase
          .from("apify_runs")
          .update({
            processing_status: "failed",
            error_message: error.message || "Unknown error",
            updated_at: new Date().toISOString(),
          })
          .eq("run_id", run_id);
      }
    } catch (updateError) {
      console.error("Error updating failed status:", updateError);
    }

    return new Response(
      JSON.stringify({
        error: error.message || "Internal server error",
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});

