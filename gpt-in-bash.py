import openai
from dotenv import load_dotenv
import subprocess
import re
import os

# OpenAI API setup
load_dotenv()
openai.api_key = os.getenv('OPEN_AI_API_KEY')

def get_gpt_response(prompt):
    response = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",  # Or the model you're using
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You will be asked for help with bash on ubuntu 20.04, if user needs to run some script you will provide such code at the end of the message you it can be parsed. You will provide only one line of script in the response and not more. If needed you will provide next script line in next promnt"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response.choices[0].message.content
def extract_bash_command(text):
    # Regular expression to match the bash code block
    match = re.search(r"```bash\s([\s\S]*?)\s```", text)
    if match:
        return match.group(1).strip()
    return None


# Function to execute Bash commands
def run_bash_command(command, venv_path=None):
    # If a virtual environment path is provided, activate it
    if command.startswith('pip'):
        if venv_path:
            # If the command starts with 'pip' and there's a virtual environment path, prepend the venv pip
            command = f"{venv_path}/bin/{command}"
    print(command)

    # Open a subprocess and run the bash command
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Initialize an empty string to accumulate output
    output = ""
    
    # Stream the output line by line
    while True:
        line = process.stdout.readline()
        if line == b"" and process.poll() is not None:
            break
        if line:
            # Decode the bytes to a string and strip newlines
            chunk = line.decode().strip()
            print(chunk)  # Print the output
            output += chunk + "\n"  # Accumulate the output with a newline

    # Get the return code of the process
    rc = process.poll()
    output += f"Return code: {rc}"
    
    return output

# Function to send terminal output back to GPT for processing
def send_output_to_gpt(output):
    prompt = f"Here is the terminal output: {output}\nWhat should I do next?"
    gpt_response = get_gpt_response(prompt)
    return gpt_response

# Main interaction loop
def interactive_bash_session():
    print("Starting...")
    #res = get_gpt_response("You will be asked for help with bash, if user needs to run some script you will provide such code at the end of the message you it can be parsed. You will provide only one line of script at the time and if needed you will provide next line in next promnt")
    #print(res)
    user_prompt = input("Enter a question or ask for a Bash command (or type 'exit' to quit): ")
    while user_prompt.lower() != 'exit':
        gpt_response = get_gpt_response(user_prompt)
        
        print(f"GPT-4 Response: {gpt_response}")

        # Ask for user confirmation before running the command
        while extract_bash_command(gpt_response) != None:

            confirmation = input(f"Do you want to run this command? (yes/no/exit): ")

            if confirmation.lower() == 'y' or confirmation.lower() == 'yes':
                bash_output = run_bash_command(extract_bash_command(gpt_response), venv_path="/home/sidsm/Zdrojaky/TerminalHelper/myenv")
    
                # Split bash output into words
                bash_output_size = bash_output.split()

                # Check if the output has more than 100 words
                if len(bash_output_size) > 100:
                    # Get the last 100 words
                    last_100_words = bash_output_size[-100:]
                    
                    # Join the last 100 words back into a string
                    bash_output = ' '.join(last_100_words)

                # Send the output back to GPT for further processing
                gpt_response = send_output_to_gpt(bash_output)
                print(f"GPT-4 Follow-up: {gpt_response}")
            elif confirmation.startswith("/"):
                run_bash_command(confirmation[1:], venv_path="/home/sidsm/Zdrojaky/TerminalHelper/myenv")
            elif confirmation.lower() == 'exit' or confirmation.lower() == 'e':
                exit(0)
            else:
                gpt_response = get_gpt_response(confirmation)
        
                print(f"GPT-4 Response: {gpt_response}")
        user_prompt = input("Enter a question or ask for a Bash command (or type 'exit' to quit): ")

if __name__ == "__main__":
    interactive_bash_session()