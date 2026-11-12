from zivra.core.commands import classify
from zivra.core.workflows import SYSTEM_REPORT, run_workflow
from zivra.plugins.manager import PluginManager

HELP = ("Local commands: open Spotify / Instagram / Phone Link / GhostLink / Chrome / browser / Files / Downloads / Settings / ChatGPT / Notepad / Calculator / Task Manager / Roblox Studio; "
        "system status; pause music; next song; previous song; volume up/down; mute. "
        "Configure executable aliases in Applications. No conversational model or account API is connected.")


class Assistant:
    def __init__(self, settings):
        self.settings = settings
        self.plugins = PluginManager(settings)

    def respond(self, command):
        try:
            intent = classify(command, self.settings.get("application_aliases"))
            if intent.action == "help":
                response = HELP
            elif intent.action == "blocked":
                response = "Command blocked. Shell commands, destructive actions and private-account access are not enabled."
            elif intent.action == "unknown":
                response = "Unrecognized local command. Type 'help'. This rule-based engine is not conversational AI."
            elif intent.action == "messages_info":
                response = "Instagram message reading is not connected. Official messaging access requires an eligible account and Meta authorization. ZIVRA does not scrape private inboxes."
            elif intent.action == "organize_info":
                response = "File organization is planned. No files were changed; a future workflow will require preview and confirmation."
            else:
                response = self.plugins.execute(intent)
        except Exception as error:
            response = f"Could not complete action: {error}"
        self.settings.record(command, response)
        return response

    def system_workflow(self):
        return run_workflow(SYSTEM_REPORT, self.plugins.execute)

    def shutdown(self):
        self.plugins.shutdown()
