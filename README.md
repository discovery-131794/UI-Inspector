# UI-Inspector

UI-Inspector is a GUI tool that can be used to view the whole windows desktop UI structure and property of every UI node.
For python developers who use uiautomation and pyjab to develop, UI-Inspector can generate tree structure and corresponding code for specified UI element.
Now, UI-Inspector supports most windows desktop applications which implemented uiautomation framework and java applications. In the future, I will try to add XML document support and maybe itegrate selenium to it.

## Installation
UI-Inspector can be installed from PYPI:

```sh
pip install uiinspector
```
then run command below:

```sh
ui-inspector
```

or you can use pyinstaller to build an executable.

Download source code from git, enter into main directory and run command below:

```sh
pyinstaller app.spec
```

## Dependencies
UI-Inspector depends on below packages:
- [PySide6](https://pypi.org/project/PySide6/)
- [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [pyjab](https://github.com/gaozhao1989/pyjab)
- [mouse](https://github.com/boppreh/mouse)
- [keyboard](https://github.com/boppreh/keyboard)

