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
    const {
      zone_id,
      location,
      search_queries,
      max_results = 3000,
      actor_id = "compass/crawler-google-places",
    } = await req.json();

    if (!zone_id || !location || !search_queries || !Array.isArray(search_queries)) {
      return new Response(
        JSON.stringify({
          error: "Missing required fields: zone_id, location, search_queries",
        }),
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

    // Get webhook URL
    const webhookUrl = `${supabaseUrl}/functions/v1/apify-webhook-handler`;

    const runs = [];
    const errors = [];

    // Start crawls for each query
    for (const query of search_queries) {
      try {
        const inputData = {
          searchStringsArray: [`${query} ${location}`],
          maxCrawledPlacesPerSearch: max_results,
          maxReviewsPerPlace: 10,
          includeImages: true,
          includeOpeningHours: true,
          language: "en",
          includeWebResults: true,
        };

        // Start the crawl
        const encodedActorId = encodeURIComponent(actor_id);
        const runResponse = await fetch(
          `https://api.apify.com/v2/acts/${encodedActorId}/runs?token=${apifyToken}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(inputData),
          }
        );

        if (!runResponse.ok) {
          const errorText = await runResponse.text();
          throw new Error(`Apify API error: ${runResponse.status} ${errorText}`);
        }

        const runData = await runResponse.json();
        const runId = runData.data.id;
        const now = new Date().toISOString();

        // Store run metadata in database
        const { error: insertError } = await supabase.from("apify_runs").insert({
          run_id: runId,
          zone_id: zone_id,
          location: location,
          query: query,
          status: "RUNNING",
          processing_status: "pending",
          started_at: runData.data.startedAt || now,
        });

        if (insertError) {
          console.error(`Error storing run ${runId}:`, insertError);
        }

        // Set up webhook for completion
        try {
          const webhookResponse = await fetch(
            `https://api.apify.com/v2/actor-runs/${runId}/webhook?token=${apifyToken}`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                eventTypes: ["ACTOR.RUN.SUCCEEDED"],
                requestUrl: webhookUrl,
                payloadTemplate: JSON.stringify({
                  data: {
                    id: "{{runId}}",
                    status: "{{status}}",
                    defaultDatasetId: "{{defaultDatasetId}}",
                    finishedAt: "{{finishedAt}}",
                    stats: {
                      itemsCount: "{{stats.itemsCount}}",
                    },
                  },
                }),
              }),
            }
          );

          if (!webhookResponse.ok) {
            console.warn(
              `Failed to set up webhook for run ${runId}:`,
              await webhookResponse.text()
            );
          }
        } catch (webhookError) {
          console.warn(`Error setting up webhook for run ${runId}:`, webhookError);
          // Don't fail the whole operation if webhook setup fails
        }

        runs.push({
          run_id: runId,
          location,
          query,
          status: "RUNNING",
          console_url: `https://console.apify.com/view/runs/${runId}`,
        });
      } catch (error) {
        console.error(`Error starting crawl for query "${query}":`, error);
        errors.push({
          query,
          error: error.message || "Unknown error",
        });
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        runs_started: runs.length,
        runs,
        errors: errors.length > 0 ? errors : undefined,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Start crawl error:", error);
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

