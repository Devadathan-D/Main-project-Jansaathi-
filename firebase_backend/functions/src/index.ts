import { genkit, z } from "genkit";
import { googleAI } from "@genkit-ai/google-genai"; // Only import the plugin
import { onCallGenkit } from "firebase-functions/https";

const ai = genkit({
  plugins: [
    googleAI({
      apiKey: process.env.GOOGLE_GENAI_API_KEY, 
    }),
  ],
  // 🔥 Use this new pattern: googleAI.model('model-name')
  model: googleAI.model('gemini-2.5-flash'), 
});

export const jansaathiChat = onCallGenkit(
  { authPolicy: () => true }, 
  ai.defineFlow(
    {
      name: "jansaathiFlow",
      inputSchema: z.object({ question: z.string() }),
      outputSchema: z.string(),
    },
    async (input) => {
      const response = await ai.generate({
        system: "You are JanSaathi, an expert on Indian government schemes.",
        prompt: input.question,
      });
      return response.text;
    }
  )
);


