from pathlib import Path
import json
from tkinter import Tk, filedialog, messagebox
from tkinter.ttk import Frame, Label, Button, Progressbar
import customtkinter as ctk

from har_parser import parse_har
from extractor import extract_api_data


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HAR to API Extractor")
        self.geometry("900x700")
        self.minsize(900, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.har_path = None
        self.output_path = None

        self.main_frame = Frame(self, padding=20)
        self.main_frame.pack(fill="both", expand=True)

        self.title_label = Label(
            self.main_frame,
            text="HAR to API Extractor",
            font=("Segoe UI", 22, "bold"),
        )
        self.title_label.pack(pady=(0, 20))

        self.select_button = Button(
            self.main_frame,
            text="Selecionar arquivo .har",
            command=self.select_har_file,
        )
        self.select_button.pack(pady=10)

        self.path_var = ctk.StringVar(value="Nenhum arquivo selecionado")
        self.path_label = ctk.CTkLabel(self.main_frame, textvariable=self.path_var)
        self.path_label.pack(pady=10)

        self.export_button = Button(
            self.main_frame,
            text="Gerar JSON",
            command=self.generate_json,
        )
        self.export_button.pack(pady=10)

        self.text_box = ctk.CTkTextbox(self.main_frame, height=30)
        self.text_box.pack(fill="both", expand=True, pady=(10, 0))
        self.text_box.insert("end", "Selecione um arquivo .har para começar.\n")

    def select_har_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo HAR",
            filetypes=[("HAR files", "*.har"), ("JSON files", "*.json")],
        )
        if file_path:
            self.har_path = file_path
            self.path_var.set(file_path)
            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", f"Arquivo selecionado: {file_path}\n")

    def generate_json(self):
        if not self.har_path:
            messagebox.showwarning("Aviso", "Selecione um arquivo .har antes.")
            return

        try:
            har_data = parse_har(self.har_path)
            extracted = extract_api_data(har_data, source_file=Path(self.har_path).name)

            save_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile="apis_extracted.json",
                filetypes=[("JSON files", "*.json")],
            )
            if not save_path:
                return

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(extracted, f, ensure_ascii=False, indent=2)

            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", f"Arquivo salvo em: {save_path}\n\n")
            self.text_box.insert("end", json.dumps(extracted, ensure_ascii=False, indent=2)[:5000])
            messagebox.showinfo("Sucesso", f"JSON gerado com sucesso em:\n{save_path}")

        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao processar o HAR:\n{exc}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
