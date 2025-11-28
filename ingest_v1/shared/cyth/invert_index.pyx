def invert(dict[str, list[int]] inverted_index) -> str:
    cdef str token
    cdef int position
    cdef list[int] positions

    cdef int abstract_length = len([1 for idxs in inverted_index.values() for _ in idxs])
    cdef list[str] abstract = [''] * abstract_length

    for token, positions in inverted_index.items():
        for position in positions:
            if position < abstract_length:
                abstract[position] = token

    return ' '.join(abstract)
