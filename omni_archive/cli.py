import argparse

def main():
    parser = argparse.ArgumentParser(
        prog='omni-archive',
        description='Universal archive extraction tool'
    )

    subparsers = parser.add_subparsers(dest='command', required=True, metavar='command')

    # --- extract subcommand ---
    extract_parser = subparsers.add_parser(
        'extract', aliases=['x'],
        help='Extract files from an archive'
    )
    extract_parser.add_argument(
        'archive',
        help='Path to the archive file'
    )
    extract_parser.add_argument(
        'members', nargs='*',
        help='Optional list of specific files to extract',
    )
    extract_parser.add_argument(
        '-C', '--directory', metavar='DIR',
        help='Change to DIR before extracting'
    )

    # --- list subcommand ---
    list_parser = subparsers.add_parser(
        'list', aliases=['l'],
        help='List contents of the archive'
    )
    list_parser.add_argument(
        'archive',
        help='Path to the archive file'
    )
    args = parser.parse_args()

    print(f"Command: {args.command}")

    if args.command in ('extract', 'x'):
        from omni_archive import Archive
        
        archive = Archive(args.archive)

        if args.directory:
            print(f"Target directory: {args.directory}")
        if args.members:
            print(f"Extracting members: {', '.join(args.members)}")
        else:
            print("Extracting all files")

    elif args.command in ('list', 'l'):
        print(f"Listing contents of: {args.archive}")

if __name__ == '__main__':
    main()
