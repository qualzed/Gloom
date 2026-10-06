import imgui

W, H = 560, 330

def rgba(r, g, b, a=255):
     return (r / 255, g / 255, b / 255, a / 255)

class Menu:
     def __init__(self):
          self.page = 0
          self.tabs = ["ESP", "AIM", "OTHERS", "GLOW"]
          self.values = {
               "hp": True, "name": True, "weapon": False,
               "skeleton": True, "box": False,
               "aim": False, "smoke": False, "flash": True,
               "glow": True
          }

     def toggle(self, name, label):
          dl = imgui.get_window_draw_list()
          p = imgui.get_cursor_screen_pos()
          x, y = p.x, p.y
          w, h = 36, 19

          imgui.invisible_button("##" + name, w, h)
          if imgui.is_item_clicked():
               self.values[name] = not self.values[name]

          on = self.values[name]
          bg = rgba(105, 118, 180) if on else rgba(48, 52, 68)
          knob = rgba(225, 230, 255) if on else rgba(135, 140, 155)

          dl.add_rect_filled(x, y, x + w, y + h, imgui.get_color_u32_rgba(*bg), h / 2)
          cx = x + (w - 10 if on else 10)
          dl.add_circle_filled(cx, y + h / 2, 6.5, imgui.get_color_u32_rgba(*knob))

          imgui.same_line()
          imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 7)
          imgui.text(label)

     def draw(self, draw_list, width, height):
          imgui.set_next_window_position((width - W) / 2, (height - H) / 2)
          imgui.set_next_window_size(W, H)

          imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 10)
          imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(13, 11))

          imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, *rgba(14, 17, 25, 235))
          imgui.push_style_color(imgui.COLOR_TEXT, *rgba(220, 222, 235))
          imgui.push_style_color(imgui.COLOR_BUTTON, *rgba(31, 34, 46, 220))
          imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *rgba(48, 53, 72, 230))
          imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *rgba(60, 66, 88, 240))

          imgui.begin("##Moonware", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

          p = imgui.get_window_position()
          dl = imgui.get_window_draw_list()
          dl.add_rect(
               p.x, p.y, p.x + W, p.y + H,
               imgui.get_color_u32_rgba(*rgba(105, 118, 180, 150)),
               10, 0, 1.0
          )

          imgui.text_colored("MOONWARE", *rgba(145, 158, 220))
          imgui.same_line()
          imgui.text_colored("// EXTERNAL (PYTHON)", *rgba(105, 109, 128))
          imgui.separator()

          for i, tab in enumerate(self.tabs):
               if i:
                    imgui.same_line()
               if i == self.page:
                    imgui.push_style_color(imgui.COLOR_BUTTON, *rgba(86, 101, 160))
                    imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *rgba(96, 112, 176))
               if imgui.button(tab, 75, 25):
                    self.page = i
               if i == self.page:
                    imgui.pop_style_color(2)

          imgui.separator()

          if self.page == 0:
               self.toggle("hp", "Draw HP")
               self.toggle("name", "Draw Name")
               self.toggle("weapon", "Draw Weapon")
               self.toggle("skeleton", "Draw Skeleton")
               self.toggle("box", "Draw Box")

          elif self.page == 1:
               self.toggle("aim", "Aimbot")
               imgui.spacing()
               imgui.text("FOV")
               imgui.slider_float("##aimfov", 90.0, 1.0, 180.0, "%.0f°")

          elif self.page == 2:
               self.toggle("smoke", "Anti Smoke")
               self.toggle("flash", "Anti Flash")
               imgui.spacing()
               imgui.text("View FOV")
               imgui.slider_float("##viewfov", 110.0, 90.0, 150.0, "%.0f°")

          elif self.page == 3:
               self.toggle("glow", "Glow")
               imgui.spacing()
               imgui.text("Glow Color")
               imgui.color_edit4(
                    "##glowcolor",
                    0.42, 0.48, 0.85, 1.0,
                    flags=imgui.COLOR_EDIT_NO_INPUTS
               )

          imgui.set_cursor_pos_y(H - 34)
          imgui.separator()
          imgui.text_colored("Moonware", *rgba(120, 125, 145))
          imgui.same_line()
          imgui.text_colored("READY", *rgba(145, 158, 220))

          imgui.end()
          imgui.pop_style_color(5)
          imgui.pop_style_var(2)