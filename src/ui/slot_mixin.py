import customtkinter as ctk

from .theme import BORDER, PANEL, SURFACE_DARK, TEXT


class SlotMixin:
    def set_multi_slot_switch(self, enabled):
        if self.widget_exists(getattr(self, "multi_slot_switch", None)):
            self.multi_slot_switch.select() if enabled else self.multi_slot_switch.deselect()

    def set_multi_slot_visible(self, enabled):
        self.update_multi_slot_visibility(enabled)

    def update_multi_slot_visibility(self, enabled):
        self.set_multi_slot_switch(enabled)
        self.is_multi_slot_visible = bool(enabled)
        if self.is_multi_slot_visible:
            self.rebuild_multi_slot_frame()
            self.multi_slot_frame.pack(fill="x", padx=12, pady=(0, 6), before=self.action_frame)
        else:
            self.destroy_multi_slot_frame()
        self.rebuild_layout()

    def rebuild_layout(self):
        target_height = self.EXPANDED_HEIGHT if self.is_multi_slot_visible else self.HEIGHT
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{self.WIDTH}x{target_height}+{x}+{y}")
        self.update_idletasks()
        self.update_child_windows_position()

    def rebuild_multi_slot_frame(self):
        self.destroy_multi_slot_frame()
        self.multi_slot_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color=PANEL,
            corner_radius=9,
            border_width=1,
            border_color=BORDER,
            height=self.SLOT_FRAME_HEIGHT,
        )
        self.slot_entries = []
        for index, label in enumerate([self.t(f"label.slot_{slot}") for slot in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0)]):
            row = ctk.CTkFrame(self.multi_slot_frame, fg_color="transparent", height=34)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, width=46, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
            entry = ctk.CTkTextbox(
                row,
                height=self.SLOT_TEXTBOX_HEIGHT,
                corner_radius=6,
                border_width=1,
                border_color="#303743",
                fg_color=SURFACE_DARK,
                text_color=TEXT,
                font=("Segoe UI", 10),
                wrap="word",
            )
            entry.insert("1.0", self.config["multi_slots"][index] if index < len(self.config["multi_slots"]) else "")
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda _event, slot_index=index, slot_entry=entry: self.controller.update_multi_slot(slot_index, slot_entry.get("1.0", "end-1c")), add="+")
            entry.bind("<FocusOut>", lambda _event, slot_index=index, slot_entry=entry: self.controller.update_multi_slot(slot_index, slot_entry.get("1.0", "end-1c")), add="+")
            self.slot_entries.append(entry)

    def destroy_multi_slot_frame(self):
        if self.widget_exists(self.multi_slot_frame):
            self.multi_slot_frame.pack_forget()
            self.multi_slot_frame.destroy()
        self.multi_slot_frame = None
        self.slot_entries = []
