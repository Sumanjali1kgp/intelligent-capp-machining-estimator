from app import create_app

app = create_app()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        app.run(debug=True)
    else:
        # For migration commands, use flask db [command] directly
        print("\n[INFO] To run migrations, use: flask db [command]")
        print("Available commands: init, migrate, upgrade, etc.")
        print("Example: flask db migrate -m 'Your message'")
        sys.exit(1)
