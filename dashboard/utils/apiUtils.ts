/**
 * Utility for handling API calls with exponential backoff retries.
 * Specially tuned for Google Gemini API limits and transient errors.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 4,
  baseDelay: number = 1500
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;
      
      const errorMessage = error?.message || '';
      const status = error?.status;

      // Detect Rate Limiting (429)
      const isRateLimit = 
        errorMessage.includes('429') || 
        errorMessage.includes('RESOURCE_EXHAUSTED') ||
        errorMessage.includes('Too Many Requests') ||
        status === 429;

      // Detect Transient Server Errors (5xx)
      const isTransientError =
        errorMessage.includes('500') ||
        errorMessage.includes('502') ||
        errorMessage.includes('503') ||
        errorMessage.includes('504') ||
        errorMessage.includes('Internal Server Error') ||
        errorMessage.includes('Service Unavailable') ||
        errorMessage.includes('Deadline Exceeded') ||
        status === 500 ||
        status === 502 ||
        status === 503 ||
        status === 504;

      // Non-retryable errors like safety blocks
      if (errorMessage.includes('SAFETY') || errorMessage.includes('blocked')) {
         console.error("AI Request blocked by safety filters:", errorMessage);
         throw new Error("The deep scan was blocked by institutional safety filters. This typically occurs during extreme market anomalies.");
      }

      // Perform retry with exponential backoff if conditions met
      if ((isRateLimit || isTransientError) && attempt < maxRetries - 1) {
        // Base backoff: 1.5s, 3s, 6s... with random jitter to prevent thundering herd
        const delay = (baseDelay * Math.pow(2, attempt)) + (Math.random() * 800);
        
        console.warn(
          `QuantAI Engine ${isRateLimit ? 'Rate Limit (429)' : 'Transient Error'}. ` +
          `Retrying in ${Math.round(delay)}ms... (Attempt ${attempt + 1}/${maxRetries})`
        );
        
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      // For all other errors (400, 401, 403, or exhausted retries)
      if (isRateLimit) {
        throw new Error("The AI processing core is currently saturated. Please wait a few seconds before initiating a new deep scan.");
      }

      if (isTransientError) {
        throw new Error("Uplink to the neural processing cluster is unstable. Please check your connection and retry.");
      }

      throw error;
    }
  }
  
  throw lastError;
}
