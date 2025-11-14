import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Get Supabase client
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Parse webhook payload
    const webhook = await req.json();
    console.log("Received webhook:", JSON.stringify(webhook, null, 2));

    // Extract run data
    const runData = webhook.data || webhook;
    const runId = runData.id;
    const status = runData.status;

    if (!runId) {
      console.error("Missing run_id in webhook payload");
      return new Response(
        JSON.stringify({ error: "Missing run_id" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Only process SUCCEEDED runs
    if (status !== "SUCCEEDED") {
      console.log(`Skipping run ${runId} with status: ${status}`);
      return new Response(
        JSON.stringify({ message: `Run ${runId} not succeeded, status: ${status}` }),
        {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Check if run already exists
    const { data: existingRun } = await supabase
      .from("apify_runs")
      .select("id, processing_status")
      .eq("run_id", runId)
      .single();

    const now = new Date().toISOString();
    const datasetId = runData.defaultDatasetId;
    const itemCount = runData.stats?.itemsCount || null;

    if (existingRun) {
      // Update existing run
      const { error: updateError } = await supabase
        .from("apify_runs")
        .update({
          status: status,
          items_count: itemCount,
          completed_at: runData.finishedAt || now,
          webhook_received_at: now,
          updated_at: now,
        })
        .eq("run_id", runId);

      if (updateError) {
        console.error("Error updating apify_runs:", updateError);
        throw updateError;
      }

      // If already processed, skip
      if (existingRun.processing_status === "completed") {
        console.log(`Run ${runId} already processed, skipping`);
        return new Response(
          JSON.stringify({ message: "Run already processed" }),
          {
            status: 200,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }
    } else {
      // Create new run record
      const { error: insertError } = await supabase
        .from("apify_runs")
        .insert({
          run_id: runId,
          status: status,
          items_count: itemCount,
          completed_at: runData.finishedAt || now,
          webhook_received_at: now,
          processing_status: "pending",
        });

      if (insertError) {
        console.error("Error inserting apify_runs:", insertError);
        throw insertError;
      }
    }

    // Invoke processing function asynchronously
    // Use Supabase function invocation or direct HTTP call
    const functionUrl = `${supabaseUrl}/functions/v1/process-apify-data`;
    const functionResponse = await fetch(functionUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${supabaseServiceKey}`,
      },
      body: JSON.stringify({
        run_id: runId,
        dataset_id: datasetId,
      }),
    }).catch((err) => {
      console.error("Error invoking process-apify-data:", err);
      // Don't fail the webhook if function invocation fails
      return null;
    });

    if (functionResponse && !functionResponse.ok) {
      console.error(
        "process-apify-data returned error:",
        await functionResponse.text()
      );
    }

    // Return success immediately (don't wait for processing)
    return new Response(
      JSON.stringify({
        success: true,
        run_id: runId,
        message: "Webhook received, processing started",
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Webhook handler error:", error);
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

