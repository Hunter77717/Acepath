import asyncio
import subprocess

async def chat_with_llama(prompt):
    command = f"echo 'Please answer briefly: {prompt}' | ollama run llama3"
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        return stdout.decode('utf-8').strip()
    else:
        print(f"Error: {stderr.decode('utf-8')}")
        return None

async def main():
    print("Chat with LLaMA 3! Type 'exit' to end the chat.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Ending chat.")
            break
        response = await chat_with_llama(user_input)
        print("LLaMA 3:", response)

# Run the async main function
asyncio.run(main())
