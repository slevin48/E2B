import streamlit as st
import openai, json
from e2b_code_interpreter import Sandbox

avatar = {
    "user": "🤓",
    "assistant": "🤖",
    "tool": "🛠️"
}

# Define the tools
tools = [{
    "type": "function",
    "function": {
        "name": "execute_python",
        "description": "Execute python code in a Jupyter notebook cell and return result",
        "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The python code to execute in a single cell"
            }
        },
            "required": ["code"]
        }
    }
}]

if "messages" not in st.session_state:
    st.session_state.messages = []

def chatbot(messages,model="gpt-4o-mini",tools=None):
    # Generate text with OpenAI
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )

    response_message = response.choices[0].message
    return dict(response_message)

def get_code(response_message):
    # Execute the tool if it's called by the model
    if response_message['tool_calls']:
        for tool_call in response_message['tool_calls']:
            if tool_call.function.name == "execute_python":
                code = json.loads(tool_call.function.arguments)['code']
                return code
@st.cache_resource
def init_sandbox():
    sandbox = Sandbox()
    return sandbox

def restart_sandbox():
    st.cache_resource.clear()
    st.session_state.sandbox = init_sandbox()
    st.success("Sandbox restarted successfully!")

if 'sandbox' not in st.session_state:
    st.session_state.sandbox = init_sandbox()

sandbox = init_sandbox()
st.sidebar.title("E2B Code Interpreter")

# Display the conversation
for msg in st.session_state.messages:
    role = msg['role']
    with st.chat_message(role, avatar=avatar[role]):
        if role == 'assistant':
            if msg['tool_calls']:
                with st.expander("Code"):
                    code = get_code(msg)
                    st.write(f"```python\n{code}\n```")
            else:
                st.write(msg['content'])
        else:
            st.write(msg['content'])

if prompt := st.chat_input("Enter a prompt"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=avatar["user"]):
        st.write(prompt)
    response_message = chatbot(st.session_state.messages,tools=tools)
    print(response_message)

    # Execute the tool if it's called by the model
    if response_message['tool_calls']:
        # Append the response message to the messages list
        st.session_state.messages.append(response_message)
        code = get_code(response_message)
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            with st.expander("Code", expanded=True):
                st.write(f"```python\n{code}\n```")
        with st.spinner("Executing code..."):
            if sandbox.is_running():
                execution = sandbox.run_code(code)
                result = execution.text
            else:
                result = 'The sandbox is not running'
        with st.chat_message("tool", avatar=avatar["tool"]):
            st.write(result)
            print(result)
            
        # Send the result back to the model
        st.session_state.messages.append({
            "role": "tool",
            "name": "execute_python",
            "content": result,
            "tool_call_id": response_message['tool_calls'][0].id,
        })

        final_response = chatbot(st.session_state.messages)
        st.session_state.messages.append(final_response)
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            st.write(final_response['content'])
        print(final_response['content'])
    else:
        st.session_state.messages.append(response_message)
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            st.write(response_message['content'])
        print(response_message['content'])
        
 
with st.sidebar:
    # Reset the conversation
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

    # Restart the sandbox
    if st.button("Restart Sandbox"):
        restart_sandbox()

    # Example of a prompt
    with st.expander("Example of a prompt"):
        st.write("Calculate the 10th element of the Fibonacci sequence.")

    # Debug
    if st.toggle('Debug', value=True):
        sandbox_state = st.session_state.sandbox.is_running()
        st.write('Sandbox state:')
        st.write("`Running`" if sandbox_state else "`Not running`")
        st.write('Session messages:')
        st.write(st.session_state.messages)
