from src.agent import AppliedMusicAgent


def main():
    print("=" * 70)
    print("  Applied AI Music Recommendation System")
    print("  CodePath AI110 — Foundations of AI Engineering")
    print("=" * 70)
    print()

    agent = AppliedMusicAgent()

    user_request = input("What kind of music are you looking for? ").strip()
    print()

    steps_input = input("Show agent reasoning steps? (y/n, default n): ").strip().lower()
    show_steps = steps_input == "y"
    print()

    print("Output style: default | professional | casual | technical")
    style_input = input("Choose style (default): ").strip().lower()
    style = style_input if style_input else "default"
    print()

    print(agent.run(user_request, show_steps=show_steps, style=style))


if __name__ == "__main__":
    main()
