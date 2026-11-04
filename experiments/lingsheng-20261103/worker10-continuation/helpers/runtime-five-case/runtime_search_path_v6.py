"""Expected environment after frozen benchmark applies its context settings."""
def expected_search_path(context,base,prefix):
    # This describes observed os.environ at setup, not the ELF loader's
    # startup search or a promise that a late assignment changes loaded DSOs.
    if not isinstance(base,str)or not base:raise ValueError('Explicit startup search path required')
    if 'LD_LIBRARY_PATH'in context:
        requested=context['LD_LIBRARY_PATH']
        if not isinstance(requested,str)or not requested:raise ValueError('Explicit nonempty context search path required')
        return requested
    return prefix+base
