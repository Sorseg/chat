import Tkinter as tk
import ttk

root = tk.Tk()


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
                        'widget': ttk.Button,
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


root.mainloop()