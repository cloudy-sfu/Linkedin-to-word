# Linkedin to word
 Convert LinkedIn profile to Microsoft Word resume

![](https://shields.io/badge/dependencies-Python_3.12-blue)

## Acknowledgement

[LinkedIn API](https://github.com/tomquirk/linkedin-api) \
[University domains list](https://github.com/Hipo/university-domains-list)

## Usage

Create a Python virtual environment, and set the program root as the current folder.

Run the following command to see CLI parameters.

```
python main.py -h
```

Based on the user's LinkedIn account and a profile ID (not necessarily owned by the LinkedIn account), generate a resume at the given file path. 

The template can be customized, where the programming language is Jinja2. The renderer is https://docxtpl.readthedocs.io/en/latest/
