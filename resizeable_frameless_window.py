from nicegui import ui, app
import win32api
import time
import threading
from win32api import GetMonitorInfo, MonitorFromPoint
from functools import partial

class MaximizeButton(ui.button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._props['icon'] = 'zoom_in_map'
        self._state = False

    def update(self) -> None:
        self.props('icon=zoom_out_map' if self._state else 'icon=zoom_in_map')
        self._state = not self._state
        super().update()


class ResizableFramelessWindow:
    def __init__(self, title, initial_dimensions=(800, 600)):
        self.title = title
        self.initial_dimensions = initial_dimensions
        self.maximized = False
        self.dimensions = initial_dimensions
        self.position = (0, 0)
        self.s_resize = None
        self.e_resize = None
        self.se_resize = None


    #-------------------------------------------------------------------------------------------------------------------
    #                                               BEHAVIOR REIMPLEMENTATION                                          |
    #-------------------------------------------------------------------------------------------------------------------

    def create_custom_div(self, style, func, direction):
        div = ui.html('<div style="{}"></div>'.format(style))

        if direction is not None:
            div.on('mousedown', partial(func, direction=direction))
        else:
            div.on('mousedown', func)

        return div

    async def on_drag_start_resize(self, event, direction):
        initial_window_pos = await app.native.main_window.get_position()
        initial_window_size = await app.native.main_window.get_size()
        threading.Thread(target=self.resize_window, args=(event, initial_window_pos, initial_window_size, direction)).start()

    def resize_window(self, event, initial_window_pos, initial_window_size, direction):
        w = direction >= 0
        h = direction <= 0
        while win32api.GetAsyncKeyState(0x01) < 0:
            cursor_x, cursor_y = win32api.GetCursorPos()

            new_width = (cursor_x - initial_window_pos[0]) * w + (initial_window_size[0] * (not w))
            new_height = (cursor_y - initial_window_pos[1]) * h + (initial_window_size[1] * (not h))

            app.native.main_window.resize(new_width, new_height)
            time.sleep(0.01)
        self.dimensions = (new_width, new_height)

    async def on_drag_start_move(self, event):
        initial_window_pos = await app.native.main_window.get_position()
        initial_mouse_pos = win32api.GetCursorPos()
        threading.Thread(target=self.move_window, args=(event, initial_window_pos, initial_mouse_pos)).start()

    def move_window(self, event, initial_window_pos, initial_mouse_pos):
        while win32api.GetAsyncKeyState(0x01) < 0:
            cursor_x, cursor_y = win32api.GetCursorPos()

            new_x = cursor_x - initial_mouse_pos[0]
            new_y = cursor_y - initial_mouse_pos[1]

            if self.maximized:
                if abs(new_x) > 25 or abs(new_y) > 25:
                    self.restore_window()
                    initial_window_pos = (self.position[0], cursor_y - new_y)

            app.native.main_window.move(initial_window_pos[0] + new_x, initial_window_pos[1] + new_y)
            time.sleep(0.01)
        if abs(new_x) > 50 or abs(new_y) > 50:
            self.position = (initial_window_pos[0] + new_x, initial_window_pos[1] + new_y)

    async def maximize_window(self):
        self.position = await app.native.main_window.get_position()
        self.maximized = True
        self.on_off_resize()
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        app.native.main_window.resize(work_area[2], work_area[3])
        time.sleep(0.05)
        app.native.main_window.move(0, 0)

    def restore_window(self):
        self.maximized = False
        self.on_off_resize()
        app.native.main_window.resize(self.dimensions[0], self.dimensions[1])
        time.sleep(0.05)
        app.native.main_window.move(self.position[0], self.position[1])

    def on_off_resize(self):
        if self.maximized:
            self.s_resize.style('pointer-events: none;')
            self.e_resize.style('pointer-events: none;')
            self.se_resize.style('pointer-events: none;')
        else:
            self.s_resize.style('pointer-events: all;')
            self.e_resize.style('pointer-events: all;')
            self.se_resize.style('pointer-events: all;')


    #-------------------------------------------------------------------------------------------------------------------
    #                                                      RUN                                                          |
    #-------------------------------------------------------------------------------------------------------------------

    def run(self):
        self.s_resize = self.create_custom_div('position: absolute; bottom: 0; left: 0; width: 100%; height: 10px; cursor: s-resize; border-bottom: 4px solid #151515;', self.on_drag_start_resize, -1)
        self.e_resize = self.create_custom_div('position: absolute; top: 0; right: 0; width: 10px; height: 100%; cursor: e-resize; border-right: 4px solid #151515;', self.on_drag_start_resize, 1)
        self.se_resize = self.create_custom_div('position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; cursor: se-resize;', self.on_drag_start_resize, 0)

        with ui.header().classes(replace='row items-center bg-dark').style('padding-right: 10px;') as header:
            ui.space()
            MaximizeButton().on('click', lambda: self.maximize_window() if not self.maximized else self.restore_window())
            ui.button(on_click=lambda: app.shutdown(), icon='close').props('flat color=red')

            header.on('mousedown', self.on_drag_start_move)

        app.native.window_args['easy_drag'] = False

        ui.run(title=self.title, native=True, frameless=True, window_size=self.initial_dimensions, reload=False)


