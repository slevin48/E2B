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
    st.session_state["messages"] = []


st.sidebar.title("E2B Code Interpreter")

# Display the conversation
for msg in st.session_state.messages:
    role = msg['role']
    with st.chat_message(role, avatar=avatar[role]):
        st.write(msg['content'])

if prompt := st.chat_input("Enter a prompt"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=avatar["user"]):
        st.write(prompt)
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    st.session_state.messages.append(dict(response_message))
    
    # Execute the function if it's called by the model
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "execute_python":
                code = json.loads(tool_call.function.arguments)['code']
                with st.chat_message("assistant", avatar=avatar["tool"]):
                    st.write(f"```python\n{code}\n```")
                with st.spinner("Executing code..."):
                    with Sandbox() as sandbox:
                        execution = sandbox.run_code(code)
                    result = execution.text
                # Send the result back to the model as a tool message
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "execute_python",
                    "content": result,
                })

        # Generate the final response
        final_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        final_message = final_response.choices[0].message
        st.session_state.messages.append(dict(final_message))
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            st.write(final_message.content)
    else:
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            st.write(response_message.content)

# Reset the conversation
if st.sidebar.button("Reset"):
    st.session_state.messages = []
    st.rerun()

# Example of a prompt
with st.sidebar.expander("Example of a prompt"):
    st.write("Calculate the 10th element of the Fibonacci sequence.")


# Debug
if st.sidebar.toggle('Debug', value=True):
    st.sidebar.write('Session messages:')
    st.sidebar.write(st.session_state.messages)
