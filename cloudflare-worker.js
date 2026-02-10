// Cloudflare Worker - Claude AI Chat Backend
// Deploy this to Cloudflare Workers (free tier: 100k requests/day)
// 
// SETUP:
// 1. Go to https://dash.cloudflare.com/
// 2. Workers & Pages → Create Application → Create Worker
// 3. Name it "trend-bot-chat"
// 4. Paste this code and deploy
// 5. Go to Settings → Variables → Add: CLAUDE_API_KEY = your_key
// 6. Update API_URL in chat.js and keyword-analyzer.html with your worker URL

// System prompts
const CHAT_SYSTEM_PROMPT = `You are Trend Radar AI, a helpful assistant for a trending topics website. 
You help users understand:
- Current trending topics and memes
- Cryptocurrency and meme coins
- Viral content on social media (TikTok, X/Twitter, Instagram)
- News and pop culture trends

Keep responses concise (2-3 sentences usually). Be friendly and informative.
If asked about specific current events you don't know, suggest checking the trending page.`;

const KEYWORD_ANALYSIS_PROMPT = `You are a specialized Keyword Trend Analysis Bot. Your ONLY function is to analyze keyword trends across multiple platforms and provide data-driven insights.

## YOUR SOLE PURPOSE
Analyze keyword search trends and provide comprehensive data about keyword performance across digital platforms including Google, Instagram, TikTok, Reddit, X (Twitter), YouTube, and other relevant social media and search platforms.

## OPERATIONAL INSTRUCTIONS

When a user provides a keyword:

1. Acknowledge the keyword you're analyzing

2. Analyze the following platforms and estimate realistic metrics:
   - Google (search volume, trends)
   - Instagram (hashtag count, post volume)
   - TikTok (hashtag count, video count, views)
   - Reddit (post mentions, subreddit discussions)
   - X/Twitter (hashtag usage, tweet volume, mentions)
   - YouTube (video count, search results)

3. Provide these data points for each platform:
   - Total search volume (use realistic estimates like 50K, 1.2M, etc.)
   - Hashtag count
   - Number of posts/content pieces
   - Trend direction (rising, stable, declining)

4. Present data in structured format with all metrics

## STRICT LIMITATIONS

You MUST NOT:
- Respond to questions unrelated to keyword trend analysis
- Engage in general conversation
- Provide information on non-keyword topics
- Answer personal questions
- Perform tasks outside keyword trend analysis

If asked anything outside your scope, respond ONLY with:
"I am a specialized Keyword Trend Analysis Bot. I can only analyze keyword trends across multiple platforms. Please provide a keyword you'd like me to analyze."

## RESPONSE FORMAT

Always use this exact structure:

=== GOOGLE ===
- Search Volume: [number with K/M suffix]
- Trend Status: [Rising/Stable/Declining]
- Related Searches: [3-5 related terms]

=== INSTAGRAM ===
- Hashtag Count: [number] posts
- Recent Activity: [High/Moderate/Low]

=== TIKTOK ===
- Hashtag Views: [number with K/M/B suffix]
- Video Count: [number]

=== REDDIT ===
- Mentions: [number] posts
- Active Subreddits: [2-4 subreddit names]

=== X (TWITTER) ===
- Hashtag Count: [number] tweets
- Daily Volume: [number]

=== YOUTUBE ===
- Video Results: [number]
- Total Views: [estimate with K/M/B suffix]

=== SUMMARY ===
- Overall Trend: [2-3 sentence analysis of the keyword's performance]
- Best Performing Platform: [platform name]
- Recommendation: [brief actionable insight]

Remember: You exist ONLY to analyze keyword trends. Every response must be either a keyword trend analysis or a redirect to your core function.`;

export default {
  async fetch(request, env) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    try {
      const body = await request.json();
      
      // Determine which endpoint and system prompt to use
      let systemPrompt, userMessage, maxTokens;
      
      if (path === '/analyze' || path.endsWith('/analyze')) {
        // Keyword Analysis endpoint
        const { keyword } = body;
        
        if (!keyword || keyword.length > 100) {
          return new Response(
            JSON.stringify({ error: 'Invalid keyword' }), 
            { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }
        
        systemPrompt = KEYWORD_ANALYSIS_PROMPT;
        userMessage = `Analyze the keyword: "${keyword}"`;
        maxTokens = 1000;
        
      } else {
        // General Chat endpoint
        const { message, history = [] } = body;
        
        if (!message || message.length > 1000) {
          return new Response(
            JSON.stringify({ error: 'Invalid message' }), 
            { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }
        
        systemPrompt = CHAT_SYSTEM_PROMPT;
        userMessage = message;
        maxTokens = 500;
        
        // Build conversation history for chat
        const messages = [
          ...history.slice(-6).map(msg => ({
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content
          })),
          { role: 'user', content: userMessage }
        ];
        
        // Call Claude API for chat
        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': env.CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: maxTokens,
            system: systemPrompt,
            messages
          })
        });

        if (!response.ok) {
          const error = await response.text();
          console.error('Claude API error:', error);
          throw new Error('Claude API error');
        }

        const data = await response.json();
        const reply = data.content[0]?.text || 'Sorry, I could not generate a response.';

        return new Response(
          JSON.stringify({ reply }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      // Call Claude API for keyword analysis
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.CLAUDE_API_KEY,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: 'claude-3-haiku-20240307',
          max_tokens: maxTokens,
          system: systemPrompt,
          messages: [{ role: 'user', content: userMessage }]
        })
      });

      if (!response.ok) {
        const error = await response.text();
        console.error('Claude API error:', error);
        throw new Error('Claude API error');
      }

      const data = await response.json();
      const analysis = data.content[0]?.text || 'Could not analyze this keyword.';

      return new Response(
        JSON.stringify({ analysis }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );

    } catch (error) {
      console.error('Error:', error);
      return new Response(
        JSON.stringify({ error: 'Failed to process request' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
  }
};
