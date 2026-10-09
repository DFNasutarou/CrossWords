def clear_cells(cells, board_size, white_state):
    for row in range(board_size):
        for col in range(board_size):
            cell = cells[row][col]
            cell.set_state(white_state)
            cell.set_char("")
            cell.set_number(None)


def clear_clue_widgets(row_title, col_title, key_groups):
    row_title.reset_square([])
    col_title.reset_square([])
    for key_group in key_groups:
        key_group.keyname.reset_square([])
        key_group.text.reset_square([])
        if hasattr(key_group.text, "reset_inline_images"):
            key_group.text.reset_inline_images([])
        key_group.text.set_text("")


def clear_title_widget(title):
    title.reset_square([])
    if hasattr(title, "reset_inline_images"):
        title.reset_inline_images([])
    title.set_text("")
