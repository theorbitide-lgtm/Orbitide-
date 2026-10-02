import json
import os
import threading
import urllib.request
import urllib.error

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


Window.softinput_mode = "below_target"

# ============================================================
# GROQ
# ============================================================

GROQ_API_KEY = ""

API_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL = "openai/gpt-oss-20b"

MEMORY_FILE = "orbitide_memory.json"


# ============================================================
# ORBITIDE PERSONALITY
# ============================================================

SYSTEM_PROMPT = """
You are ORBITIDE, a personal AI assistant.

You are intelligent, calm, direct, curious and helpful.

Answer the user's actual question instead of simply repeating it.

You can help with general questions, science, technology,
programming, writing, ideas, learning, planning and conversation.

Use the user's saved memories when they are relevant.

Do not claim to remember something unless it is actually in memory.

Be honest when you do not know something.

Keep normal answers reasonably concise.
"""


# ============================================================
# BRAIN
# ============================================================

class OrbitideBrain:

    def __init__(self, memory_path):

        self.memory_path = memory_path
        self.memory = {}
        self.pending_memory = None
        self.conversation = []

        self.load_memory()


    # ========================================================
    # MEMORY FILE
    # ========================================================

    def load_memory(self):

        try:

            if os.path.exists(self.memory_path):

                with open(
                    self.memory_path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    self.memory = json.load(file)

        except Exception:

            self.memory = {}


    def save_memory(self):

        try:

            with open(
                self.memory_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.memory,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception:

            pass


    # ========================================================
    # MEMORY DISPLAY
    # ========================================================

    def memory_text(self):

        if not self.memory:
            return "No saved memories yet."

        lines = []

        for key, value in self.memory.items():

            if key == "name":

                lines.append(
                    "The user's name is "
                    + str(value)
                    + "."
                )

            else:

                lines.append(
                    "The user asked ORBITIDE to remember: "
                    + str(value)
                    + "."
                )

        return "\n".join(lines)


    # ========================================================
    # AUTOMATIC MEMORY DETECTION
    # ========================================================

    def detect_memory(self, text):

        lower = text.lower().strip()

        # NAME
        if "my name is " in lower:

            position = lower.find("my name is ")

            value = text[
                position + len("my name is "):
            ].strip()

            if value:
                return "name", value


        # WHERE USER LIVES
        if "i live in " in lower:

            position = lower.find("i live in ")

            value = text[
                position + len("i live in "):
            ].strip()

            if value:
                return "location", value


        # WORK
        if "i work as " in lower:

            position = lower.find("i work as ")

            value = text[
                position + len("i work as "):
            ].strip()

            if value:
                return "work", value


        # STUDY
        if "i study " in lower:

            position = lower.find("i study ")

            value = text[
                position + len("i study "):
            ].strip()

            if value:
                return "study", value


        # LIKES
        if "i like " in lower:

            position = lower.find("i like ")

            value = text[
                position + len("i like "):
            ].strip()

            if value:
                return "preference", "Likes " + value


        # LOVES
        if "i love " in lower:

            position = lower.find("i love ")

            value = text[
                position + len("i love "):
            ].strip()

            if value:
                return "preference", "Loves " + value


        # FAVORITES
        if "my favorite " in lower:

            position = lower.find("my favorite ")

            value = text[
                position + len("my favorite "):
            ].strip()

            if value:
                return "favorite", value


        return None


    # ========================================================
    # LOCAL COMMANDS + MEMORY
    # ========================================================

    def local_command(self, text):

        lower = text.lower().strip()


        # ----------------------------------------------------
        # WAITING FOR YES / NO
        # ----------------------------------------------------

        if self.pending_memory is not None:

            if lower in (
                "yes",
                "y",
                "yes please",
                "sure",
                "okay",
                "ok"
            ):

                key = self.pending_memory["key"]
                value = self.pending_memory["value"]

                self.memory[key] = value

                self.save_memory()

                self.pending_memory = None

                return (
                    "Saved forever. "
                    "I will remember that."
                )


            if lower in (
                "no",
                "n",
                "nope"
            ):

                self.pending_memory = None

                return "Okay. I won't save it."


            return (
                "Please say YES to save it, "
                "or NO to cancel."
            )


        # ----------------------------------------------------
        # EXPLICIT "REMEMBER THAT"
        # ----------------------------------------------------

        if lower.startswith("remember that"):

            value = text[
                len("remember that"):
            ].strip()

            if value:

                number = 1

                while "fact_" + str(number) in self.memory:
                    number += 1

                self.pending_memory = {
                    "key": "fact_" + str(number),
                    "value": value
                }

                return (
                    "I can remember that.\n\n"
                    "Should I remember forever? "
                    "Say YES."
                )


        # ----------------------------------------------------
        # AUTOMATIC MEMORY
        # ----------------------------------------------------

        detected = self.detect_memory(text)

        if detected is not None:

            key, value = detected

            self.pending_memory = {
                "key": key,
                "value": value
            }

            return (
                "I can remember that.\n\n"
                + str(value)
                + "\n\n"
                "Should I remember forever? "
                "Say YES."
            )


        # ----------------------------------------------------
        # WHO AM I
        # ----------------------------------------------------

        if lower in (
            "who am i",
            "who am i?",
            "what is my name",
            "what is my name?",
            "what's my name",
            "what's my name?"
        ):

            if "name" in self.memory:

                return (
                    "Your name is "
                    + str(self.memory["name"])
                    + ".\n\n"
                    "I remember that."
                )

            return (
                "I don't know your name yet.\n\n"
                "Tell me: my name is ..."
            )


        # ----------------------------------------------------
        # WHAT DO YOU REMEMBER
        # ----------------------------------------------------

        if lower in (
            "what do you remember",
            "what do you remember?",
            "show my memory",
            "show me what you remember",
            "what have you remembered"
        ):

            return self.memory_text()


        # ----------------------------------------------------
        # CLEAR MEMORY
        # ----------------------------------------------------

        if lower in (
            "forget everything",
            "forget all my memories",
            "clear my memory"
        ):

            self.memory = {}

            self.save_memory()

            return "All saved memories have been cleared."


        return None


    # ========================================================
    # AI
    # ========================================================

    def ask_ai(self, user_text):

        messages = [

            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + "\n\nSAVED MEMORY:\n"
                    + self.memory_text()
                )
            }

        ]


        messages.extend(
            self.conversation[-20:]
        )


        messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )


        payload = {

            "model": MODEL,

            "messages": messages,

            "temperature": 0.7,

            "max_completion_tokens": 2048
        }


        data = json.dumps(
            payload
        ).encode("utf-8")


        request = urllib.request.Request(

            API_URL,

            data=data,

            method="POST",

            headers={

                "Authorization":
                    "Bearer " + GROQ_API_KEY,

                "Content-Type":
                    "application/json",

                "Accept":
                    "application/json",

                "User-Agent":
                    "ORBITIDE/1.0"
            }
        )


        try:

            with urllib.request.urlopen(
                request,
                timeout=60
            ) as response:

                raw = response.read().decode(
                    "utf-8"
                )

                result = json.loads(raw)


            reply = (
                result["choices"][0]
                ["message"]["content"]
            )


            self.conversation.append(
                {
                    "role": "user",
                    "content": user_text
                }
            )


            self.conversation.append(
                {
                    "role": "assistant",
                    "content": reply
                }
            )


            return reply


        except urllib.error.HTTPError as error:

            try:
                body = error.read().decode("utf-8")
            except Exception:
                body = "No details."

            return (
                "ORBITIDE connection error.\n\n"
                "HTTP "
                + str(error.code)
                + "\n\n"
                + body
            )


        except urllib.error.URLError as error:

            return (
                "ORBITIDE cannot reach the AI.\n\n"
                "Check your internet connection.\n\n"
                + str(error)
            )


        except Exception as error:

            return (
                "ORBITIDE error:\n\n"
                + str(error)
            )


# ============================================================
# APP
# ============================================================

class OrbitideApp(App):

    def build(self):

        memory_path = os.path.join(
            self.user_data_dir,
            MEMORY_FILE
        )

        self.brain = OrbitideBrain(
            memory_path
        )


        root = BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=10
        )


        self.chat_history = Label(

            text=(
                "[b]ORBITIDE[/b]\n\n"
                "I am ready."
            ),

            markup=True,

            size_hint_y=None,

            text_size=(None, None),

            halign="left",

            valign="top"
        )


        self.chat_history.bind(
            texture_size=self.update_chat_size
        )


        self.scroll = ScrollView(
            size_hint=(1, 1)
        )

        self.scroll.add_widget(
            self.chat_history
        )


        bottom = BoxLayout(

            orientation="horizontal",

            size_hint_y=None,

            height=55,

            spacing=5
        )


        self.input_box = TextInput(

            hint_text="Talk to ORBITIDE...",

            multiline=False,

            size_hint_x=0.8
        )


        self.send_button = Button(

            text="SEND",

            size_hint_x=0.2
        )


        self.send_button.bind(
            on_press=self.send_message
        )


        self.input_box.bind(
            on_text_validate=self.send_message
        )


        bottom.add_widget(
            self.input_box
        )

        bottom.add_widget(
            self.send_button
        )


        root.add_widget(
            self.scroll
        )

        root.add_widget(
            bottom
        )


        return root


    # ========================================================
    # SIZE
    # ========================================================

    def update_chat_size(
        self,
        instance,
        value
    ):

        instance.height = value[1]

        if self.chat_history.parent:

            instance.text_size = (
                self.chat_history.parent.width - 20,
                None
            )


    # ========================================================
    # SEND
    # ========================================================

    def send_message(
        self,
        instance=None
    ):

        text = self.input_box.text.strip()

        if not text:
            return


        self.add_message(
            "YOU",
            text
        )


        self.input_box.text = ""

        self.send_button.disabled = True

        self.send_button.text = "..."


        local_reply = self.brain.local_command(
            text
        )


        if local_reply is not None:

            self.add_message(
                "ORBITIDE",
                local_reply
            )

            self.send_button.disabled = False

            self.send_button.text = "SEND"

            return


        thread = threading.Thread(

            target=self.ai_thread,

            args=(text,),

            daemon=True
        )

        thread.start()


    # ========================================================
    # AI THREAD
    # ========================================================

    def ai_thread(self, text):

        reply = self.brain.ask_ai(text)

        Clock.schedule_once(

            lambda dt:
            self.show_reply(reply),

            0
        )


    # ========================================================
    # SHOW REPLY
    # ========================================================

    def show_reply(self, reply):

        self.add_message(
            "ORBITIDE",
            reply
        )

        self.send_button.disabled = False

        self.send_button.text = "SEND"


    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message(
        self,
        speaker,
        message
    ):

        self.chat_history.text = (

            self.chat_history.text

            + "\n\n[b]"
            + speaker
            + ":[/b] "

            + message
        )


        self.chat_history.texture_update()


        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )


    def scroll_bottom(self, dt):

        self.scroll.scroll_y = 0


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    OrbitideApp().run()
