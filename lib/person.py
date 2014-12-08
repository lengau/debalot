"""Methods for handling a Person."""


def parse_person(output_field, input_string):
    """Parse a person string into an appropriate Person protobuf.

    Args:
        output_field: The protobuf into which to parse the person.
        input_string: The string from which to parse the person.
    """
    # TODO: Copy an existing person field if it exists, based on email address.
    #       Perhaps we should give each Person an ID and reference them by ID.
    email_start = input_string.find('<')
    email_end = input_string.find('>')
    output_field.name = input_string[:email_start].strip()
    output_field.email = input_string[email_start+1:email_end]
