import streamlit as st
import tempfile
import os
import re
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from pptx import Presentation

# Page configuration
st.set_page_config(
    page_title="SmartPrep AI",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #0a0f1e 0%, #0c1222 100%);
    }
    .chat-message-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        padding: 12px 18px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-end;
        margin-left: auto;
    }
    .chat-message-ai {
        background: rgba(30, 41, 70, 0.85);
        color: #f0f3ff;
        padding: 12px 18px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-start;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton button {
        background: #3b82f6;
        color: white;
        border-radius: 25px;
        padding: 8px 20px;
    }
    .stTextInput input {
        background: rgba(255,255,255,0.07);
        color: black;
        border-radius: 25px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "ai", "content": "Hello! I'm SmartPrep AI. Upload your PDF, DOC, PPT files and I will extract text from them. Ask me questions about the content. Choose a mode above to customize your study experience."}
    ]

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "exam"

if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = ""

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = ""

if "process_button_text" not in st.session_state:
    st.session_state.process_button_text = "Process Document"

# Sidebar - Modes
with st.sidebar:
    st.markdown("## Study Mode")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Exam Prep", use_container_width=True):
            st.session_state.current_mode = "exam"
            st.session_state.messages.append({"role": "ai", "content": "Exam Prep mode activated. I will help you prepare for tests with practice questions and key concepts."})
            st.rerun()
    
    with col2:
        if st.button("Topic Prep", use_container_width=True):
            st.session_state.current_mode = "topic"
            st.session_state.messages.append({"role": "ai", "content": "Topic Prep mode activated. I will provide detailed explanations and structured learning."})
            st.rerun()
    
    with col3:
        if st.button("Brush Up", use_container_width=True):
            st.session_state.current_mode = "brushup"
            st.session_state.messages.append({"role": "ai", "content": "Brush Up mode activated. I will give quick reviews and memory aids."})
            st.rerun()
    
    st.markdown("---")
    st.markdown("## Upload Document")
    
    uploaded_file = st.file_uploader("Upload PDF, DOCX, or PPTX file", type=['pdf', 'docx', 'pptx', 'txt'])
    
    if uploaded_file is not None:
        if st.button(st.session_state.process_button_text, use_container_width=True):
            with st.spinner("Processing document..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()
                extracted_text = ""
                
                try:
                    if file_extension == 'pdf':
                        # Use pypdf (works on Streamlit Cloud)
                        pdf_reader = PdfReader(uploaded_file)
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() + "\n"
                    
                    elif file_extension == 'txt':
                        extracted_text = uploaded_file.read().decode('utf-8')
                    
                    elif file_extension == 'docx':
                        doc = Document(BytesIO(uploaded_file.read()))
                        for para in doc.paragraphs:
                            extracted_text += para.text + "\n"
                    
                    elif file_extension == 'pptx':
                        prs = Presentation(BytesIO(uploaded_file.read()))
                        for slide in prs.slides:
                            for shape in slide.shapes:
                                if hasattr(shape, "text"):
                                    extracted_text += shape.text + "\n"
                    
                    if extracted_text and len(extracted_text) > 50:
                        st.session_state.uploaded_file_content = extracted_text
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.session_state.process_button_text = "Processed"
                        
                        preview = extracted_text[:300]
                        st.session_state.messages.append({
                            "role": "ai",
                            "content": f"Successfully processed '{uploaded_file.name}'\n\nDocument contains {len(extracted_text)} characters.\n\nPreview:\n\"{preview}...\"\n\nYou can now ask me questions about this document."
                        })
                    else:
                        st.session_state.messages.append({
                            "role": "ai",
                            "content": f"Could not extract text from '{uploaded_file.name}'. The file may be image-based or encrypted. Try a text-based PDF or TXT file."
                        })
                    
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "ai",
                        "content": f"Error processing file: {str(e)}"
                    })
                
                st.rerun()
    
    st.markdown("---")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "ai", "content": "Chat cleared! How can I help you study today?"}
        ]
        st.rerun()

# Main chat area
st.markdown("# SmartPrep AI")
st.markdown("Ask questions about your document - I'll find and show you the exact content.")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-message-user">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-ai">{message["content"]}</div>', unsafe_allow_html=True)

# Generate response by extracting EXACT content from PDF
def generate_response(user_question, mode, file_content, file_name):
    
    if not file_content or len(file_content) < 50:
        return f"No document loaded. Please upload a PDF file using the sidebar first."
    
    question_lower = user_question.lower()
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', file_content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    # Extract keywords from question
    stop_words = ['what', 'is', 'are', 'the', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'by', 'at', 'from', 'this', 'that', 'these', 'those', 'and', 'or', 'but', 'so', 'because', 'if', 'then', 'else', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how']
    keywords = [w for w in question_lower.split() if w not in stop_words and len(w) > 2]
    
    if not keywords:
        keywords = question_lower.split()[:3]
    
    # Find sentences containing keywords
    matching_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        match_count = 0
        for keyword in keywords:
            if keyword in sentence_lower:
                match_count += 1
        if match_count > 0:
            matching_sentences.append({
                "sentence": sentence,
                "matches": match_count
            })
    
    # Sort by relevance
    matching_sentences.sort(key=lambda x: x["matches"], reverse=True)
    
    # Handle different question types
    if "summar" in question_lower or "summary" in question_lower:
        summary = ". ".join(sentences[:10])
        return f"Summary of '{file_name}':\n\n{summary}..."
    
    elif "key point" in question_lower or "important" in question_lower or "main" in question_lower:
        if matching_sentences:
            result = f"Key Points from '{file_name}':\n\n"
            for i, match in enumerate(matching_sentences[:8], 1):
                result += f"{i}. {match['sentence']}.\n\n"
            return result
        else:
            return f"Key Points from '{file_name}':\n\n" + "\n\n".join([f"{i+1}. {s}." for i, s in enumerate(sentences[:8])])
    
    elif "what" in question_lower or "explain" in question_lower or "describe" in question_lower:
        if matching_sentences:
            result = f"From '{file_name}':\n\n"
            for i, match in enumerate(matching_sentences[:5], 1):
                result += f"{i}. {match['sentence']}.\n\n"
            return result
        else:
            preview = file_content[:800]
            return f"No exact match found for: \"{user_question}\"\n\nHere's what your document contains:\n\n\"{preview}...\"\n\nTry asking with different keywords from your document."
    
    else:
        if matching_sentences:
            result = f"Answer from '{file_name}':\n\n"
            for i, match in enumerate(matching_sentences[:5], 1):
                result += f"{i}. {match['sentence']}.\n\n"
            return result
        else:
            preview = file_content[:600]
            return f"Your question: \"{user_question}\"\n\nNo exact match found.\n\nHere's what your document contains:\n\n\"{preview}...\"\n\nTry asking:\n- 'Summarize this document'\n- 'What are the key points?'\n- Or use keywords that appear in your document"

# Chat input
st.markdown("---")

# Use form for auto-clear
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Ask a question about your document...",
        key="user_input",
        label_visibility="collapsed",
        placeholder="Type your question here..."
    )
    submit_button = st.form_submit_button("Send", use_container_width=False)
    
    if submit_button and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Generate AI response
        if st.session_state.uploaded_file_content:
            response = generate_response(
                user_input,
                st.session_state.current_mode,
                st.session_state.uploaded_file_content,
                st.session_state.uploaded_file_name
            )
        else:
            response = "Please upload a document first using the sidebar. Once uploaded, I can answer questions based on its content."
        
        # Add AI response
        st.session_state.messages.append({"role": "ai", "content": response})
        st.rerun()
