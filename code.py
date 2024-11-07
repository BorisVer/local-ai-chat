import openai
import tkinter as tk
from tkinter import scrolledtext, filedialog
import chardet
from dotenv import load_dotenv
import os
from PIL import Image, ImageTk
import base64
import re

load_dotenv()
# This can be "Nemo" or "DeepSeek" depending on what you use
ai = "Nemo" # DeepSeek atm broken

# Get the key from env and the url for the correct ai
if ai == "Nemo":
    key = os.getenv("MY_NEMOTRON_KEY")
    url = os.getenv("MY_NEMOTRON_URL")
    llm_model = "nvidia/llama-3.1-nemotron-70b-instruct"
    stream_value = True
elif ai == "DeepSeek":
    key = os.getenv("MY_DEEPSEEK_KEY")
    url = os.getenv("MY_DEEPSEEK_URL")
    llm_model = "deepseek-chat"
    stream_value = False

# Initialize the client
client = openai.OpenAI(api_key=key, base_url=url)

# Edit this to make custom first prompt
content = 'Your my assistant. FORMAT OVERRIDE INITIATE. SESSION FORMAT PREFERENCES: CUSTOM: APPLY FOLLOWING RULES FOR THIS SESSION (AND FUTURE SESSIONS UNTIL FURTHER NOTICE):1. **Headings**: éHeading Texté. All headings are the same. DO NOT USE ** 2. ``` code snippet ```: ½ code snippet ½. END OF OVERRIDE DECLARATION'
conversation_history = [{"role": "system", "content": content}]
currently_code = False
currently_bold = False
currently_heading = False

def send_message(message, image_data=None):
    print("Sendnig step 1: Start message sending process")
    global conversation_history

    if image_data:  # If image data is present
        message = f"Uploaded image: (base64 encoded data omitted for brevity)\nDescribe the image here: [Your description of the image]"

    conversation_history.append({"role": "user", "content": message})

    print("Sending step 2: Send chat history to " + url)
    response = client.chat.completions.create(
        model= llm_model,
        messages=conversation_history,
        stream=stream_value
    )
    deepseek_message = get_response(response)
    print("Sending step 3: Answer recieved, done")
    conversation_history.append({"role": "assistant", "content": deepseek_message})
    return deepseek_message

# Get response with code depending on the ai in use
def get_response(response):
    if ai == "Nemo":
        response_text = ""
        global currently_code
        update_chat_history(ai + ": ")
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
                update_chat_history_live(chunk.choices[0].delta.content)
                window.update_idletasks() 
                print(chunk.choices[0].delta.content, end="")
        #update_chat_history(response_text)
        currently_code = False
        return response_text
    elif ai == "DeepSeek":
        update_chat_history(response.choices[0].message.content)
        window.update_idletasks() 
        return response.choices[0].message.content


def upload_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        try:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                print("Error: Image sending not yet working")
                return None
                # Handle image files for sending to DeepSeek
                with open(file_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                # Display the image in the chat
                image = Image.open(file_path)
                image.thumbnail((500, 500))
                photo = ImageTk.PhotoImage(image)
                chat_history.image_create(tk.END, image=photo)
                chat_history.insert(tk.END, "\n")
                chat_history.image = photo

                deepseek_message = send_message(f"User uploaded an image: {file_path}", encoded_image)  # 

            else:
                # Handle text files
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

                with open(file_path, 'r', encoding=encoding) as file:
                    file_content = file.read()
                deepseek_message = ("File uploaded: " + file_path + "\n" + file_content)

            conversation_history.append({"role": "assistant", "content": deepseek_message})
            print("File uploaded")
            return deepseek_message

        except Exception as e:
            print(f"Error: {e}")
            error_message = "Error reading or processing file: " + str(e)
            chat_history.configure(state="normal")
            chat_history.insert(tk.END, error_message + "\n", "deepseek")
            chat_history.configure(state="disabled")
            return error_message

def upload_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        try:
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    try:
                        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                            print("Error: Image sending not yet working")
                            continue
                            # Handle image files for sending to DeepSeek
                            with open(file_path, "rb") as image_file:
                                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                            # Display the image in the chat
                            image = Image.open(file_path)
                            image.thumbnail((500, 500))
                            photo = ImageTk.PhotoImage(image)
                            chat_history.image_create(tk.END, image=photo)
                            chat_history.insert(tk.END, "\n")
                            chat_history.image = photo

                            deepseek_message = send_message(f"User uploaded an image: {file_path}", encoded_image)

                        else:
                            # Handle text files
                            with open(file_path, 'rb') as file:
                                raw_data = file.read()
                            result = chardet.detect(raw_data)
                            encoding = result['encoding']

                            with open(file_path, 'r', encoding=encoding) as file:
                                file_content = file.read()
                            deepseek_message = ("File uploaded: " + file_path + "\n" + file_content)

                        conversation_history.append({"role": "assistant", "content": deepseek_message})
                        print("File uploaded")

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        error_message = "Error reading or processing file: " + str(e)
                        chat_history.configure(state="normal")
                        chat_history.insert(tk.END, error_message + "\n", "deepseek")
                        chat_history.configure(state="disabled")

        except Exception as e:
            print(f"Error: {e}")
            error_message = "Error reading or processing folder: " + str(e)
            chat_history.configure(state="normal")
            chat_history.insert(tk.END, error_message + "\n", "deepseek")
            chat_history.configure(state="disabled")

    print("Entire Folder Uploaded")


def on_send_click():
    user_message = user_input.get("1.0", tk.END).strip()
    if user_message:
        chat_history.configure(state="normal")
        chat_history.insert(tk.END, "\n" + "You: " + user_message + "\n", "user")
        chat_history.configure(state="disabled")
        # Send the chat and wait for answer
        send_message(user_message)
        user_input.delete("1.0", tk.END)
        global conversation_history

def check_for_code(text):

    match = re.search(r"½(.*?)½", text, re.DOTALL) # re.DOTALL allows matching across multiple lines

    if match:
        code = match.group(1).strip()  # Extract and clean the code
        before_code = text[:match.start()].strip()
        after_code = text[match.end():].strip()

        return {
            "before": before_code,
            "code": code,
            "after": after_code
        }
    else:
        return {"text": text} 

# Update the chat interface and change the visuals of text depending on the tag
def update_chat_history(text):
    tag = "deepseek"
    table = check_for_code(text)
    
    chat_history.configure(state="normal")
    chat_history.configure(state="disabled")

    if "code" in table:
        chat_history.insert(tk.END, table["before"], tag)
        chat_history.insert(tk.END, table["code"], "code")
        chat_history.insert(tk.END, table["after"], tag)
    else:
        chat_history.insert(tk.END, text, tag)

    chat_history.see(tk.END)

def update_chat_history_live(text, tag='deepseek'):
    if text == None:
        return
    # Check if need to update currently_code
    if "½" in text:
        global currently_code
        if currently_code:
            currently_code = False
            return
        else:
            currently_code = True
            return 
    # Check if need to update currently_bold
    elif "ī" in text:
        global currently_bold
        if currently_bold:
            currently_bold = False
            return
        else:
            currently_bold = True
            return 
    # Check if need to update currently_heading
    elif "é" in text:
        global currently_heading
        if currently_heading:
            currently_heading = False
            return
        else:
            currently_heading = True
            return 
    if currently_heading:
        tag = "heading"
    if currently_bold:
        tag = "bold"
    if currently_code:
        tag = "code"
    chat_history.configure(state="normal")
    chat_history.insert(tk.END, text, tag)

    chat_history.configure(state="disabled")
    chat_history.see(tk.END) 

def clear_chat_history():
    global conversation_history
    chat_history.configure(state="normal")
    chat_history.delete("1.0", tk.END)  # Clear the text widget
    chat_history.configure(state="disabled")
    conversation_history = [{"role": "system", "content": content}]

# --- Styling ---
BG_COLOR = "#F5F5F5"  # Light gray background
USER_TEXT_COLOR = "#27ae60"  # Blue for user
DEEPSEEK_TEXT_COLOR = "#3498db" # Green for DeepSeek
CODE_TEXT_COLOR = "#e74c3c"  # Red for code
FONT = ("Helvetica", 12) # Normal font
BOLD_FONT = ("Helvetica", 12, "bold") # Bold font
HEADING_FONT = ("Helvetica", 15) # Heading font



# Create main window
window = tk.Tk()
window.title(ai + " Chat")
window.configure(bg=BG_COLOR)  # Set background color for the whole window

# Chat history display
chat_history = scrolledtext.ScrolledText(window, wrap=tk.WORD, state="disabled", bg=BG_COLOR, font=FONT, borderwidth=0)
chat_history.tag_configure("user", foreground=USER_TEXT_COLOR, font=FONT)
chat_history.tag_configure("deepseek", foreground=DEEPSEEK_TEXT_COLOR, font=FONT)
chat_history.tag_configure("code", foreground=CODE_TEXT_COLOR, font=("Courier", 12))  # Monospace font for code
chat_history.tag_configure("bold", foreground=DEEPSEEK_TEXT_COLOR, font=BOLD_FONT)  # Monospace font for bold
chat_history.tag_configure("heading", foreground=DEEPSEEK_TEXT_COLOR, font=HEADING_FONT)
chat_history.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# User input area
user_input = scrolledtext.ScrolledText(window, wrap=tk.WORD, height=5, width=70, bg="white", font=FONT, borderwidth=1, relief="solid")
user_input.pack(fill=tk.X, padx=10, pady=(0, 10))  # Fill horizontally

# Add an "Upload File" button:
upload_file_button = tk.Button(window, text="Upload File", command=upload_file, bg=USER_TEXT_COLOR, fg="white", relief="raised", font=FONT)
upload_file_button.pack(pady=(0, 10))

# Add a entire folder
upload_folder_button = tk.Button(window, text="Upload Folder", command=upload_folder, bg=USER_TEXT_COLOR, fg="white", relief="raised", font=FONT)
upload_folder_button.pack(side=tk.LEFT, pady=(0, 10)) # Put it next to the "Send" button

# Button frame for Send and Clear History buttons
button_frame = tk.Frame(window, bg=BG_COLOR)
button_frame.pack(pady=(0, 10))

# Send button
send_button = tk.Button(button_frame, text="Send", command=on_send_click, bg=USER_TEXT_COLOR, fg="white", relief="raised", font=FONT)
send_button.pack(side=tk.LEFT, padx=(0, 10))

# Clear history button
clear_button = tk.Button(button_frame, text="Clear History", command=clear_chat_history, bg=USER_TEXT_COLOR, fg="white", relief="raised", font=FONT)
clear_button.pack(side=tk.RIGHT)

# Start the GUI
window.mainloop()