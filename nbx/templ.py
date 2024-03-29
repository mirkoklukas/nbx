# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/03_templ.ipynb.

# %% auto 0
__all__ = ['get_templ_args', 'render_templ', 'create_file_from_template', 'render_template_from_string']

# %% ../notebooks/03_templ.ipynb 2
from pathlib import Path
import jinja2, jinja2.meta as meta


def get_templ_args(path):
    path = Path(path)
    loader = jinja2.FileSystemLoader(searchpath=str(path.parent))
    env = jinja2.Environment(loader=loader)

    src = env.loader.get_source(env, path.name)[0]
    parsed = env.parse(src)
    args = meta.find_undeclared_variables(parsed)

    return args


def render_templ(path, vars):
    path = Path(path)
    loader = jinja2.FileSystemLoader(searchpath=str(path.parent))
    env    = jinja2.Environment(loader=loader)

    template = env.get_template(path.name)
    text = template.render(vars)  
    return text


def create_file_from_template(tpath, fpath, vars):
    script_src = render_templ(tpath, vars)

    with open(fpath, "w", newline="\n") as f:
            f.write(script_src)

def render_template_from_string(s, vars):
    template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(s)
    return template.render(vars)
