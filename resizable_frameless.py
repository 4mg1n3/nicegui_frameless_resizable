from nicegui import ui, app
import win32api
import time
import threading
from win32api import GetMonitorInfo, MonitorFromPoint





#----------------------------------------------------
#    Custom drag zone to move and resize the window |
#----------------------------------------------------

def create_custom_div(style, func):
    div = ui.html('<div style="{}"></div>'.format(style))
    
    div.on('mousedown', func)

    return div

#----------------------------------------------------
# We resize and move the window in a separate thread |
#----------------------------------------------------
async def on_drag_start_resize(event):
    initial_window_pos = await app.native.main_window.get_position()
    threading.Thread(target=resize_window, args=(event, initial_window_pos)).start()

def resize_window(event, initial_window_pos):

    # while the left mouse button is pressed
    while win32api.GetAsyncKeyState(0x01) < 0:
        cursor_x, cursor_y = win32api.GetCursorPos()

        new_width = cursor_x - initial_window_pos[0]
        new_height = cursor_y - initial_window_pos[1]

        app.native.main_window.resize(new_width, new_height)
        time.sleep(0.01)

async def on_drag_start_move(event):
    initial_window_pos = await app.native.main_window.get_position()
    initial_mouse_pos = win32api.GetCursorPos()
    threading.Thread(target=move_window, args=(event, initial_window_pos, initial_mouse_pos)).start()

def move_window(event, initial_window_pos, initial_mouse_pos):
    while win32api.GetAsyncKeyState(0x01) < 0:
        cursor_x, cursor_y = win32api.GetCursorPos()

        new_x = cursor_x - initial_mouse_pos[0]
        new_y = cursor_y - initial_mouse_pos[1]
        

        app.native.main_window.move(initial_window_pos[0] + new_x, initial_window_pos[1] + new_y)
        time.sleep(0.01)

def maximize_window():
    monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
    work_area = monitor_info.get("Work")
    app.native.main_window.resize(work_area[2], work_area[3])
    time.sleep(0.1)
    app.native.main_window.move(0, 0)

#----------------------------------------------------
#    Styling                                         |
#----------------------------------------------------

# We create the different drag zones
create_custom_div('position: absolute; bottom: 0; left: 0; width: 100%; height: 10px; cursor: s-resize; border-bottom: 4px solid #151515;', on_drag_start_resize)
create_custom_div('position: absolute; top: 0; right: 0; width: 10px; height: 100%; cursor: e-resize; border-right: 4px solid #151515;', on_drag_start_resize)
create_custom_div('position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; cursor: se-resize;', on_drag_start_resize)


with ui.header().classes(replace='row items-center bg-dark').style('padding-right: 10px;') as header:
    with ui.tabs() as tabs:
        ui.tab('A')
        ui.tab('B')
        ui.tab('C')
    ui.space()
    ui.button(on_click=maximize_window, icon='crop_square').props('flat color=white')
    ui.button(on_click=lambda: app.shutdown(), icon='close').props('flat color=red')

    # We assign the move event to the header
    header.on('mousedown', on_drag_start_move)

    


app.native.window_args['easy_drag'] = False

ui.run(title='Resizable Frameless Window', native=True, frameless=True, window_size=(800, 600), reload=False)

