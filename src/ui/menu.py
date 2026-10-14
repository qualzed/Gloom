import imgui
from internal import header

W, H = 560, 360

BINDINGS = {
    "hp": "_esp_hp", "name": "_esp_name", "weapon": "_esp_weapon",
    "skeleton": "_esp_bones", "box": "_esp_box",
    "aim": "_aim", "trigger": "_trigger",
    "smoke": "_antismoke", "flash": "_antiflash", "fov": "_fov", "bhop": "_bhop",
    "glow": "_glow",
}

DEFAULTS = {
    "_aim_fov": 90.0,
    "_view_fov": 110.0,
    "_esp_color": (1.0, 1.0, 1.0),
    "_glow_color": (0.42, 0.48, 0.85),
}

def rgba(r, g, b, a=255):
    return (r / 255, g / 255, b / 255, a / 255)

def load_settings():
    try:
        from internal import serializer
        return serializer
    except Exception:
        return None
class Menu:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else load_settings()
        self.page = 0
        self.tabs = ["ESP", "AIM", "OTHERS", "GLOW"]

    # --- settings access ---
    def get(self, name, default=None):
        return getattr(self.settings, name, DEFAULTS.get(name, default))

    def set(self, name, value):
        setattr(self.settings, name, value)

        save = getattr(self.settings, "save", None)
        if callable(save):
            save()

    # --- widgets ---
    def toggle(self, name, label):
        attr = BINDINGS[name]
        dl = imgui.get_window_draw_list()
        p = imgui.get_cursor_screen_pos()
        x, y = p.x, p.y
        w, h = 36, 19

        imgui.invisible_button("##" + name, w, h)
        if imgui.is_item_clicked():
            self.set(attr, not bool(self.get(attr, False)))

        on = bool(self.get(attr, False))
        bg = rgba(105, 118, 180) if on else rgba(48, 52, 68)
        knob = rgba(225, 230, 255) if on else rgba(135, 140, 155)

        dl.add_rect_filled(x, y, x + w, y + h, imgui.get_color_u32_rgba(*bg), h / 2)
        cx = x + (w - 10 if on else 10)
        dl.add_circle_filled(cx, y + h / 2, 6.5, imgui.get_color_u32_rgba(*knob))

        imgui.same_line()
        imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 7)
        imgui.text(label)

    def slider(self, attr, label, low, high):
        imgui.text(label)
        imgui.push_item_width(W - 40)
        changed, value = imgui.slider_float("##" + attr, float(self.get(attr, low)), low, high, "%.0f")
        imgui.pop_item_width()
        if changed:
            self.set(attr, value)

    def color(self, attr, label):
        imgui.text(label)
        imgui.same_line()
        r, g, b = self.get(attr, (1.0, 1.0, 1.0))[:3]
        changed, value = imgui.color_edit3("##" + attr, r, g, b, flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed:
            self.set(attr, tuple(value))

    # --- pages ---
    def page_esp(self):
        for name, label in (("hp", "Draw HP"), ("name", "Draw Name"), ("weapon", "Draw Weapon"),
                            ("skeleton", "Draw Skeleton"), ("box", "Draw Box")):
            self.toggle(name, label)
        imgui.spacing()
        self.color("_esp_color", "ESP Color")

    def page_aim(self):
        self.toggle("aim", "Aimbot")
        self.toggle("trigger", "Triggerbot")
        imgui.spacing()
        self.slider("_aim_fov", "FOV", 1.0, 180.0)

    def page_others(self):
        self.toggle("smoke", "Anti Smoke")
        self.toggle("flash", "Anti Flash")
        self.toggle("bhop", "Bunnyhop")
        self.toggle("fov", "View FOV changer")
        imgui.spacing()
        self.slider("_view_fov", "View FOV", 90.0, 150.0)

    def page_glow(self):
        self.toggle("glow", "Glow")
        imgui.spacing()
        self.color("_glow_color", "Glow Color")

    # --- window ---
    def draw(self, draw_list, width, height):
        imgui.set_next_window_position((width - W) / 2, (height - H) / 2, imgui.FIRST_USE_EVER)
        imgui.set_next_window_size(W, H)

        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 10)
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(13, 11))

        imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, *rgba(14, 17, 25, 235))
        imgui.push_style_color(imgui.COLOR_TEXT, *rgba(220, 222, 235))
        imgui.push_style_color(imgui.COLOR_BUTTON, *rgba(31, 34, 46, 220))
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *rgba(48, 53, 72, 230))
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *rgba(60, 66, 88, 240))

        imgui.begin(f"##{header.SOFT_NAME}".upper(), flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE |
                    imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_SAVED_SETTINGS)

        p = imgui.get_window_position()
        dl = imgui.get_window_draw_list()
        dl.add_rect(p.x, p.y, p.x + W, p.y + H, imgui.get_color_u32_rgba(*rgba(105, 118, 180, 150)), 10, 0, 1.0)

        imgui.text_colored(f"{header.SOFT_NAME}".upper(), *rgba(145, 158, 220))
        imgui.same_line()
        imgui.text_colored("// EXTERNAL (PYTHON)", *rgba(105, 109, 128))
        imgui.separator()

        for i, tab in enumerate(self.tabs):
            if i:
                imgui.same_line()

            selected = i == self.page
            if selected:
                imgui.push_style_color(imgui.COLOR_BUTTON, *rgba(86, 101, 160))
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *rgba(96, 112, 176))
            clicked = imgui.button(tab, 75, 25)
            if selected:
                imgui.pop_style_color(2)

            if clicked:
                self.page = i

        imgui.separator()

        (self.page_esp, self.page_aim, self.page_others, self.page_glow)[self.page]()

        imgui.set_cursor_pos_y(H - 34)
        imgui.separator()
        imgui.text_colored(f"{header.SOFT_NAME}", *rgba(120, 125, 145))
        imgui.same_line()
        imgui.text_colored("READY", *rgba(145, 158, 220))

        imgui.end()
        imgui.pop_style_color(5)
        imgui.pop_style_var(2)