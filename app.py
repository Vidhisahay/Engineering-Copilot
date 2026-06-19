from flask import Flask, render_template, jsonify, request, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.chat_memory import append_turn, format_history_for_input
from src.metrics import init_metrics
from dotenv import load_dotenv
import os


def _build_rag_chain():
    from src.helper import download_hugging_face_embeddings
    from langchain_pinecone import PineconeVectorStore
    from langchain_openai import ChatOpenAI
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    from src.prompts import system_prompt

    embeddings = download_hugging_face_embeddings()

    index_name = "engineering-copilot"

    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
    )

    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    chat_model = ChatOpenAI(model="gpt-4o")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(
        chat_model,
        prompt
    )

    return create_retrieval_chain(
        retriever,
        question_answer_chain
    )


def create_app(config_overrides=None, rag_chain=None):
    app = Flask(__name__)

    load_dotenv()

    app.config.update(
        {
            "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY", "change-me-in-production"),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "change-me-in-production"),
            "AUTH_USERNAME": os.environ.get("AUTH_USERNAME", "admin"),
            "AUTH_PASSWORD": os.environ.get("AUTH_PASSWORD", "password"),
            "CHAT_RATE_LIMIT": os.environ.get("CHAT_RATE_LIMIT", "20 per minute"),
        }
    )

    if config_overrides:
        app.config.update(config_overrides)

    init_metrics(app)
    JWTManager(app)

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        storage_uri="memory://",
    )

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if pinecone_api_key:
        os.environ["PINECONE_API_KEY"] = pinecone_api_key
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key

    if rag_chain is None:
        rag_chain = _build_rag_chain()

    app.rag_chain = rag_chain

    @app.route("/")
    def index():
        return render_template("chat.html")

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")

        if (
            username != app.config["AUTH_USERNAME"]
            or password != app.config["AUTH_PASSWORD"]
        ):
            return jsonify({"msg": "Invalid username or password"}), 401

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    @app.route("/get", methods=["GET", "POST"])
    @limiter.limit(lambda: app.config["CHAT_RATE_LIMIT"])
    @jwt_required()
    def chat():
        msg = request.form["msg"]
        history = session.get("chat_history", [])
        model_input = format_history_for_input(history, msg)

        response = rag_chain.invoke({"input": model_input})
        answer = str(response["answer"])

        session["chat_history"] = append_turn(history, msg, answer)
        session.modified = True

        return answer

    print("\nREGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(rule)

    return app


if os.environ.get("SKIP_APP_INIT") != "1":
    app = create_app()
else:
    app = None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
