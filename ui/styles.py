"""
ui/styles.py
Colour and font constants for the VaultKey Tkinter UI.
"""

# Colours
BG_DARK      = "#0D1117"    # main background
BG_SECONDARY = "#161B22"    # sidebar / card background
BG_INPUT     = "#0D1117"    # input field background
ACCENT       = "#58D4C8"    # teal accent
ACCENT_BTN   = "#0E7490"    # button colour
TEXT_PRIMARY = "#C9D1D9"    # main text
TEXT_MUTED   = "#8B949E"    # secondary text
BORDER       = "#30363D"    # border colour
DANGER       = "#F85149"    # red for delete/error
SUCCESS      = "#3FB950"    # green for success

# Strength colours
STRENGTH_COLOURS = {
    0: "#E24B4A",   # very weak
    1: "#F0883E",   # weak
    2: "#EF9F27",   # fair
    3: "#3FB950",   # good
    4: "#58D4C8",   # strong
}

# Fonts
FONT_TITLE   = ("Segoe UI", 24, "bold")
FONT_HEADING = ("Segoe UI", 14, "bold")
FONT_BODY    = ("Segoe UI", 11)
FONT_SMALL   = ("Segoe UI", 9)
FONT_BUTTON  = ("Segoe UI", 11, "bold")
FONT_MONO    = ("Courier New", 11)

# Apply consistent styling to a butto
def style_button(btn, danger=False, secondary=False):
   
    if danger:
        bg = DANGER
    elif secondary:
        bg = BG_SECONDARY
    else:
        bg = ACCENT_BTN

    btn.configure(
        bg=bg,
        fg=TEXT_PRIMARY,
        font=FONT_BUTTON,
        relief="flat",
        cursor="hand2",
        padx=16,
        pady=8,
        borderwidth=0,
        activebackground=ACCENT,
        activeforeground=TEXT_PRIMARY,
    )

# Apply consistent styling to an input field
def style_entry(entry):
    entry.configure(
        bg=BG_INPUT,
        fg=TEXT_PRIMARY,
        font=FONT_BODY,
        relief="flat",
        insertbackground=TEXT_PRIMARY,
        highlightthickness=1,
        highlightcolor=ACCENT,
        highlightbackground=BORDER,
    )

# Apply consistent styling to a label
def style_label(label, muted=False, heading=False, title=False):
    if title:
        font = FONT_TITLE
    elif heading:
        font = FONT_HEADING
    else:
        font = FONT_BODY

    label.configure(
        bg=BG_DARK,
        fg=TEXT_MUTED if muted else TEXT_PRIMARY,
        font=font,
    )