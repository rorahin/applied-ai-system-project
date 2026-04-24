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
    print(agent.run(user_request))


if __name__ == "__main__":
    main()
