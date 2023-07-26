def invert(dict[str, list[int]] inverted_index, int abstract_length) -> str:
    cdef str token
    cdef int position
    cdef list[int] positions
    cdef list[str] abstract = [''] * abstract_length

    for token, positions in inverted_index.items():
        for position in positions:
            if position < abstract_length:
                abstract[position] = token

    return ' '.join(abstract)
