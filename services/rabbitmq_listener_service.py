"""
RabbitMQ listener for inactive-warnings queue
Receives messages from Flink and prints user_id and email information
"""
import json
import pika
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId

from database.db_connection import user_db
from config.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VIRTUAL_HOST,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
)

INACTIVE_WARNINGS_QUEUE = "inactive-warnings"

connection = None
channel = None


# -----------------------------------------------------------
#  EMAIL (Using SSL 465)
# -----------------------------------------------------------
def send_email(to_email: str, subject: str, html_content: str):
    """Send email using SMTP_SSL (Correct for 163 Email)"""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)

        server.login(SMTP_USER, SMTP_PASSWORD)

        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()


    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")


# -----------------------------------------------------------
#  DATABASE
# -----------------------------------------------------------
def get_user_from_db(user_id: str) -> dict:
    if user_db is None:
        print("[ERROR] user_db is None !")
        return None

    try:
        try:
            user_object_id = ObjectId(user_id)
        except:
            user_object_id = user_id

        user = user_db["users"].find_one({"_id": user_object_id}, {"password_hash": 0})

        if user:
            return {
                "id": str(user.get("_id", "")),
                "email": user.get("email"),
                "username": user.get("username"),
            }
        return None

    except Exception as e:
        print("[DB ERROR]", e)
        return None


# -----------------------------------------------------------
#  MESSAGE PARSER
# -----------------------------------------------------------
def parse_message(message_body: str):
    try:
        data = json.loads(message_body)
        uid = data.get("userId") or data.get("user_id")
        return {"user_id": uid, "raw_data": data}
    except:
        print(f"[ERROR] Not JSON message: {message_body}")
        return None


# -----------------------------------------------------------
#  MESSAGE HANDLER
# -----------------------------------------------------------
def on_message_received(ch, method, properties, body):
    try:
        msg = body.decode("utf-8")
        print("\n" + "=" * 60)
        print("[RECEIVED]", msg)
        print("=" * 60)

        parsed = parse_message(msg)
        if not parsed:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        user_id = parsed["user_id"]
        if not user_id:
            print("[WARNING] No user_id found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print("Querying DB for user:", user_id)
        user = get_user_from_db(user_id)

        if not user:
            print("[WARNING] User not found:", user_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print("[SUCCESS] User found:", user)

        # ---------- SEND EMAIL ----------
        if user["email"]:
            html = f"""
            <h2>Inactive Warning</h2>
            <p>Hello <b>{user['username']}</b>,</p>
            <p>You registered but did not start a chat within the required time.</p>
            <p>Please return soon 😊</p>
            """
            send_email(
                to_email=user["email"],
                subject="⚠ Inactive Warning Notification",
                html_content=html
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("[ERROR] Message Process Error:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# -----------------------------------------------------------
#  START LISTENING
# -----------------------------------------------------------
def start_listening():
    global connection, channel

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VIRTUAL_HOST,
                credentials=credentials,
            )
        )

        channel = connection.channel()
        channel.queue_declare(queue=INACTIVE_WARNINGS_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=INACTIVE_WARNINGS_QUEUE,
            on_message_callback=on_message_received
        )

        print("[INFO] Listening on:", INACTIVE_WARNINGS_QUEUE)
        channel.start_consuming()

    except Exception as e:
        print("[ERROR] Listener crashed:", e)
        sys.exit(1)


# -----------------------------------------------------------
#  STOP LISTENING
# -----------------------------------------------------------
def stop_listening():
    global connection, channel

    try:
        if channel and channel.is_open:
            channel.stop_consuming()
        if connection and connection.is_open:
            connection.close()
    except Exception as e:
        print("[Shutdown ERROR]:", e)

    print("[Shutdown] Listener stopped.")


# -----------------------------------------------------------
#  Standalone
# -----------------------------------------------------------
if __name__ == "__main__":
    start_listening()
