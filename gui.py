import Tkinter as tk
import ttk

root = tk.Tk()

def connect():
    pass


def host():
    pass


def disable_chat():
    userlist['bg']='grey'
    text['bg']='grey'
    text['state']='disabled'


def enable_chat():
    userlist['bg']='white'
    text['bg']='white'
    text['state']='normal'


def show_options():
    '''show options window'''
    if root.options_window.winfo_exists():
        root.options_window.deiconify()
        return

    root.options_window = tk.Toplevel(takefocus=True)
    root.options_window.title('Options')

    login_label = ttk.Label(root.options_window, text='Login:')
    login_label.grid(row=0,column=0)

    root.login = ttk.Entry(root.options_window)
    root.login.insert(0,'User')
    root.login.grid(row=0, column=1)

    connect_button = ttk.Button(root.options_window,
        text='Connect', command=connect)

    connect_button.grid(row=1, column=0)

    root.address = ttk.Entry(root.options_window)
    root.address.insert(0,'sorseg.dyndns.org')
    root.address.grid(row=1, column=1)

    host_button = ttk.Button(root.options_window,
        text='Host', command=host)
    host_button.grid(row=2, column=0)

    root.options_window.lift()
    root.options_window.deiconify()


def build_from_dict(tkd, root):
    """Builds tkinter app from dictionary"""
    result = {}

    for k, v in tkd.items():
        pack = {'fill': 'both'}
        pack.update(v.get('pack', {}))

        holder = tk.Frame(root)
        holder.pack(pack)

        widget = v['widget'](holder, **v.get('args', {}))
        widget.pack(expand=1, fill='both', side='left')
        result[k] = {'widget': widget}

        if 'y' in v.get('scroll', ''):
            scrolly = ttk.Scrollbar(holder, orient='vertical')
            result[k]['scrolly'] = scrolly
            scrolly.pack(side='right', fill='y', expand=0)

            scrolly['command'] = widget.yview
            widget['yscrollcommand'] = scrolly.set

        if 'children' in v:
            result[k].update(build_from_dict(v['children'], widget))
            continue
    return result


widgets_dict = {
    'top frame': {
        'widget': tk.Frame, 'pack': {'side': 'top', 'expand': 1},
        'children': {
            'messages': {
                'widget': tk.Text,
                'args': {'state': 'disabled', 'wrap': 'word'},
                'pack': {'side': 'left', 'expand': 1, 'fill': 'both'},
                'scroll': 'y'
            },
            'right frame': {
                'widget': tk.Frame,
                'pack': {'side': 'right', 'fill': 'y'},
                'children': {
                    'options': {
                        'widget': ttk.Button, 'command': show_options,
                        'args': {'text': 'options'},
                        'pack': {'side': 'top'}
                    },
                    'users': {
                        'widget': tk.Listbox,
                        'scroll': 'y',
                        'pack': {'side': 'bottom', 'fill': 'y', 'expand': 1}
                    }
                }
            }

        }
    },
    'bottom frame': {
        'widget': tk.Frame, 'pack': {'side': 'bottom'},
        'children': {
            'text': {
                'widget': tk.Text,
                'args': {'height': 3, 'width': 50},
                'pack': {'side': 'left', 'fill': 'x', 'expand': 1}
            },
            'send': {
                'widget': ttk.Button,
                'args': {'text': 'Send'},
                'pack': {'side': 'right'}
            }
        }
    }
}

root.widgets = build_from_dict(widgets_dict, root)

userlist = root.widgets['top frame']['right frame']['users']['widget']
text = root.widgets['bottom frame']['text']['widget']
messages = root.widgets['top frame']['messages']['widget']

root.options_window = tk.Toplevel()
root.options_window.destroy()

root.after(50, show_options)

disable_chat()
root.mainloop()