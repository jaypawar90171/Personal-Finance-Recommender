import json
import google.genai as genai # New import
from google.genai import types # New import for types
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf
import os

# --- Configuration and Setup ---

# Load API Key\
client = genai.Client(api_key='AIzaSyDdlD0YPw4KWYz34KA0u-yOuOy6Mu9Rqm8')

api_key = None # Initialize api_key to None
try:
    api_key = open('GOOGLE_API_KEY.txt', 'r').read().strip()
    if not api_key:
        st.error("API key file 'GOOGLE_API_KEY.txt' is empty.")
        st.stop()
    # Removed: genai.configure(api_key=api_key) # This function doesn't exist in google.genai
    st.success("Google AI API key loaded successfully.") # Keep success message for loading
except FileNotFoundError:
    st.error("API key file 'GOOGLE_API_KEY.txt' not found. Please create it and add your key.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while loading the API key: {e}")
    st.stop()

# --- Stock Data Functions (No changes needed from original) ---

# ... (Keep your stock data functions as they are) ...
def get_stock_price(ticker):
    """Gets the latest closing stock price for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        if history.empty:
            return f"Could not retrieve data for ticker: {ticker}. It might be invalid or delisted."
        return str(history.iloc[-1].Close)
    except Exception as e:
        return f"Error fetching stock price for {ticker}: {e}"

def calculate_SMA(ticker, window):
    """Calculates the Simple Moving Average (SMA) for a given ticker and window."""
    try:
        data = yf.Ticker(ticker).history(period="1y").Close
        if data.empty:
            return f"Could not retrieve data for ticker: {ticker} for SMA calculation."
        if len(data) < window:
            return f"Not enough data points ({len(data)}) for window size {window} for ticker {ticker}."
        return str(data.rolling(window=window).mean().iloc[-1])
    except Exception as e:
        return f"Error calculating SMA for {ticker}: {e}"

def calculate_EMA(ticker, window):
    """Calculates the Exponential Moving Average (EMA) for a given ticker and window."""
    try:
        data = yf.Ticker(ticker).history(period="1y").Close
        if data.empty:
             return f"Could not retrieve data for ticker: {ticker} for EMA calculation."
        if len(data) < window: # EMA technically works but gives less meaningful results early on
              st.warning(f"Data points ({len(data)}) might be less than ideal for EMA window size {window} for ticker {ticker}.")
        return str(data.ewm(span=window, adjust=False).mean().iloc[-1])
    except Exception as e:
        return f"Error calculating EMA for {ticker}: {e}"

def calculate_RSI(ticker):
    """Calculates the Relative Strength Index (RSI) for a given ticker."""
    try:
        data = yf.Ticker(ticker).history(period="1y").Close
        if data.empty:
              return f"Could not retrieve data for ticker: {ticker} for RSI calculation."
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        # Handle division by zero if loss is zero
        rs = gain / loss.replace(0, 1e-10) # Add small epsilon to avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        # Handle potential NaNs if not enough data for rolling window
        if pd.isna(rsi.iloc[-1]):
              return f"Could not calculate RSI for {ticker}, likely due to insufficient data for the 14-day window."
        return str(rsi.iloc[-1])
    except Exception as e:
        return f"Error calculating RSI for {ticker}: {e}"

def calculate_MACD(ticker):
    """Calculates the Moving Average Convergence Divergence (MACD) for a given ticker."""
    try:
        data = yf.Ticker(ticker).history(period="1y").Close
        if data.empty:
              return f"Could not retrieve data for ticker: {ticker} for MACD calculation."
        exp1 = data.ewm(span=12, adjust=False).mean()
        exp2 = data.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal
        # Handle potential NaNs if not enough data
        if pd.isna(macd.iloc[-1]) or pd.isna(signal.iloc[-1]) or pd.isna(macd_hist.iloc[-1]):
              return f"Could not calculate MACD components for {ticker}, likely due to insufficient data."
        return f'MACD: {macd.iloc[-1]:.2f}, Signal: {signal.iloc[-1]:.2f}, Histogram: {macd_hist.iloc[-1]:.2f}'
    except Exception as e:
        return f"Error calculating MACD for {ticker}: {e}"

def plot_stock_price(ticker):
    """Plots the stock price for the last year for a given ticker and saves it."""
    try:
        data = yf.Ticker(ticker).history(period="1y")
        if data.empty:
            return f"Could not retrieve data for ticker: {ticker} to plot."

        plt.figure(figsize=(10, 5))
        plt.plot(data.index, data['Close'], label=f'{ticker} Close Price') # Use 'Close' column
        plt.title(f'{ticker} Stock Price (Last 1 Year)')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)') # Assuming USD, adjust if needed
        plt.legend()
        plt.grid(True)
        plt.tight_layout() # Adjust layout to prevent labels overlapping
        # Ensure the plot directory exists if needed
        # if not os.path.exists('plots'):
        #     os.makedirs('plots')
        plot_filename = f'{ticker}_stock_price.png'
        plt.savefig(plot_filename)
        plt.close() # Close the plot to free memory
        return f"Plot saved as {plot_filename}"
    except Exception as e:
        return f"Error plotting stock price for {ticker}: {e}"

# --- Gemini Function Declarations ---

# Map Python functions to callable names for the model
available_functions = {
    "get_stock_price": get_stock_price,
    "calculate_SMA": calculate_SMA,
    "calculate_EMA": calculate_EMA,
    "calculate_RSI": calculate_RSI,
    "calculate_MACD": calculate_MACD,
    "plot_stock_price": plot_stock_price,
}

# Describe the functions for the Gemini model
# Use types.Tool and types.FunctionDeclaration
tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_stock_price",
            description="Get the current/latest closing stock price of a given ticker symbol.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'AAPL' for Apple, 'GOOGL' for Google).",
                    }
                },
                "required": ["ticker"],
            },
        ),
        types.FunctionDeclaration(
            name="calculate_SMA",
            description="Calculate the Simple Moving Average (SMA) for a given stock ticker over a specified window period.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'AAPL', 'MSFT').",
                    },
                    "window": {
                        "type": "integer",
                        "description": "The number of days (window size) for the SMA calculation (e.g., 20, 50).",
                    },
                },
                "required": ["ticker", "window"],
            },
        ),
        types.FunctionDeclaration(
            name="calculate_EMA",
            description="Calculate the Exponential Moving Average (EMA) for a given stock ticker over a specified window period.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'AAPL', 'TSLA').",
                    },
                    "window": {
                        "type": "integer", # Technically span for ewm, but 'window' is intuitive here
                        "description": "The number of days (span) for the EMA calculation (e.g., 12, 26).",
                    },
                },
                "required": ["ticker", "window"],
            },
        ),
        types.FunctionDeclaration(
            name="calculate_RSI",
            description="Calculate the Relative Strength Index (RSI) for a given stock ticker. RSI is typically calculated over a 14-day period.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'NVDA', 'AMD').",
                    }
                },
                "required": ["ticker"],
            },
        ),
        types.FunctionDeclaration(
            name="calculate_MACD",
            description="Calculate the Moving Average Convergence Divergence (MACD) indicator for a given stock ticker. Returns MACD line, Signal line, and Histogram value.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'GOOG', 'AMZN').",
                    }
                },
                "required": ["ticker"],
            },
        ),
        types.FunctionDeclaration(
            name="plot_stock_price",
            description="Generate and save a plot of the closing stock price over the last year for a given ticker.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., 'META', 'NFLX').",
                    }
                },
                "required": ["ticker"],
            },
        ),
    ]
)

# --- Gemini Model Interaction ---

# Initialize the Gemini model (using gemini-1.5-flash for speed/cost, or gemini-pro)
# Pass the api_key directly to the constructor
# Add safety settings to block harmful content
# Use types.HarmCategory and types.HarmBlockThreshold
safety_settings = {
    types.HarmCategory.HARM_CATEGORY_HARASSMENT: types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# model = genai.GenerativeModel(
#     model_name="gemini-1.5-flash",
#     tools=[tools],
#     safety_settings=safety_settings,
#     api_key=api_key # Pass the API key here
#     )

# Start a chat session (keeps context if needed, though we'll handle calls explicitly)
# chat = model.start_chat() # We might not need stateful chat for simple requests

def get_gemini_response(user_prompt):
    """Sends prompt to Gemini, handles function calls, returns final response."""
    st.session_state.plot_filename = None # Reset plot filename for this request
    try:
        # Send the initial prompt to the model
        response = client.models.generate_content( model='gemini-2.0-flash-001', contents=user_prompt)
        # response = model.generate_content(user_prompt)

        # Check if the model returned a function call or text
        # Safely access parts, in case candidates or content is None/empty
        response_parts = []
        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             response_parts = response.candidates[0].content.parts


        # Iterate through parts to find potential function calls
        text_response = ""
        processed_function_calls = [] # To keep track of calls made in this turn

        for part in response_parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                # Access args directly, they are a dict-like object
                function_args = {key: value for key, value in function_call.args.items()}

                processed_function_calls.append((function_name, function_args))

            if hasattr(part, 'text'):
                text_response += part.text # Append text parts

        # Process the collected function calls
        for function_name, function_args in processed_function_calls:
             if function_name in available_functions:
                 # Call the corresponding Python function
                 function_to_call = available_functions[function_name]
                 st.info(f"🤖 Calling function: {function_name}({function_args})")
                 try:
                     function_response_content = function_to_call(**function_args)

                     # Special handling for plot: store filename for display
                     if function_name == "plot_stock_price" and "saved as" in function_response_content:
                         # Extract filename (handle potential errors)
                         try:
                             # Assumes format "Plot saved as FILENAME"
                             filename = function_response_content.split("saved as ")[1]
                             if os.path.exists(filename):
                                 st.session_state.plot_filename = filename
                             else:
                                 st.warning(f"Plot function reported saving {filename}, but file not found.")
                                 st.session_state.plot_filename = None # Ensure it's None if file missing
                         except IndexError:
                              st.warning("Could not parse filename from plot function response.")
                              st.session_state.plot_filename = None


                 except Exception as e:
                     st.error(f"Error executing function {function_name}: {e}")
                     function_response_content = f"Error during execution: {e}"

                 # Prepare the function response Part for Gemini
                 # Use types.Part.from_function_response
                 function_response_part = types.Part.from_function_response(
                     name=function_name,
                     response={"content": function_response_content} # API expects response content here
                 )

                 # Send the function call and response back to the model
                 st.info(f"📩 Sending function result back to Gemini...")
                 # Construct the history for the next turn
                 # The history should include the user's original prompt, the model's response with the tool call,
                 # and the tool's response.
                 # Note: In a real chat session, you would append messages to a chat history object
                 # and then send the entire history to the model. For this request/response pattern,
                 # we reconstruct the necessary history for the model to understand the tool call context.

                 # Get the Content object from the model's response that contained the function call
                 model_response_content_with_tool_call = None
                 if response and response.candidates and response.candidates[0].content:
                     model_response_content_with_tool_call = response.candidates[0].content

                 if model_response_content_with_tool_call:
                     history_for_next_turn = [
                         types.Content(role='user', parts=[types.Part.from_text(user_prompt)]),
                         model_response_content_with_tool_call, # Model's response with the tool call
                         types.Content(role='user', parts=[function_response_part]) # Tool response is typically 'user' role
                     ]
                     response = model.generate_content(history_for_next_turn)

                     # After sending the tool response, the model should ideally return text.
                     # We get the new response and extract the text part.
                     text_response = "" # Reset text response as we expect new text after tool call
                     if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                          # Assuming the model's final response is text after the tool call
                          for part in response.candidates[0].content.parts:
                              if hasattr(part, 'text'):
                                  text_response += part.text
                     else:
                          text_response = "The model did not return a text response after the tool execution."

                 else:
                      st.error("Could not find model's response content to send back with function result.")
                      return "An internal error occurred while processing the tool call."


             else:
                 st.error(f"Model requested unknown function: {function_name}")
                 return "Sorry, I tried to use a tool I don't recognize."

        # If no function calls were processed, the initial text_response captured earlier is used.
        # If function calls were processed, text_response was updated after the last model call.
        if text_response:
             return text_response
        else:
             # This might happen if the model only returned function calls and no text initially or after tool call
             return "Received a response structure I couldn't interpret as text."


    except Exception as e:
        st.error(f"An error occurred interacting with the Gemini model: {e}")
        # Log the full error for debugging if needed: print(f"Gemini Error: {e}")
        # Check for specific API errors (e.g., quota, invalid key)
        if "API key not valid" in str(e) or "authentication" in str(e).lower():
             return "The provided Google AI API key is invalid. Please check GOOGLE_API_KEY.txt."
        elif "resource has been exhausted" in str(e).lower() or "quota" in str(e).lower():
             return "The Google AI API quota has been exceeded. Please check your usage limits or try again later."
        return "Sorry, I encountered an error while processing your request."


# --- Streamlit UI ---
def show_assistant(user_id):
    st.title("📈 Stock Analysis Assistant (with Gemini AI)")
    st.caption("Ask about stock prices, SMA, EMA, RSI, MACD, or request a price plot.")

    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "plot_filename" not in st.session_state:
        st.session_state.plot_filename = None

    # Display prior chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If a plot was generated for this bot message, display it
            if message["role"] == "assistant" and "plot" in message and message["plot"]:
                if os.path.exists(message["plot"]):
                    st.image(message["plot"])
                else:
                    st.warning(f"Tried to display plot {message['plot']}, but the file is missing.")


    # Get user input
    user_query = st.chat_input("Ask me about a stock (e.g., 'What is the price of AAPL?', 'Plot MSFT', 'Calculate 50 day SMA for GOOGL')")

    if user_query:
        # Add user message to chat history and display it
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Get response from Gemini
        with st.spinner("Thinking..."):
            assistant_response_text = get_gemini_response(user_query)
            plot_generated = st.session_state.plot_filename # Capture if a plot was generated

        # Add assistant response to chat history and display it
        # Include plot filename if one was created during this turn
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response_text,
            "plot": plot_generated # Store path to plot file if created
            })

        with st.chat_message("assistant"):
            st.markdown(assistant_response_text)
            # Display the plot if one was generated *for this specific response*
            if plot_generated:
                if os.path.exists(plot_generated):
                    st.image(plot_generated)
                else:
                    # This might happen if the file saving failed silently earlier
                    st.warning(f"Assistant mentioned a plot ({plot_generated}), but the file could not be found.")

        # Clean up the temporary plot file variable for the next run
        st.session_state.plot_filename = None

    # --- Example Usage of Gemini Model (Updated for new library) ---

    # This part is just for demonstration, remove if not needed in your Streamlit app flow
    prompt_text = "What is the current stock price of AAPL?"
    try:
        # Pass the API key here as well if you use this block
        response = genai.generate_content(prompt_text, api_key=api_key)
        print(response.text)
    except Exception as e:
        print(f"Error in example usage: {e}")