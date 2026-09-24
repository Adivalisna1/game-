import random
import time
import itertools

SUITS = ['♥️ Hearts', '♦️ Diamonds', '♣️ Clubs', '♠️ Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]
        
    def __str__(self):
        return f"{self.rank} {self.suit.split()[0]}"
        
    def __repr__(self):
        return self.__str__()

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for r in RANKS for s in SUITS]
        random.shuffle(self.cards)
        
    def draw(self, n=1):
        drawn = []
        for _ in range(n):
            if self.cards:
                drawn.append(self.cards.pop())
        return drawn[0] if n == 1 else drawn

def evaluate_hand(hand):
    values = sorted([card.value for card in hand], reverse=True)
    suits = [card.suit for card in hand]
    
    is_flush = len(set(suits)) == 1
    
    is_straight = False
    if len(set(values)) == 5 and values[0] - values[-1] == 4:
        is_straight = True
    elif values == [14, 5, 4, 3, 2]: # A-2-3-4-5 straight
        is_straight = True
        values = [5, 4, 3, 2, 1]
        
    counts = {v: values.count(v) for v in set(values)}
    counts_sorted = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    
    if is_flush and is_straight: return (8, values)
    if counts_sorted[0][1] == 4: return (7, counts_sorted[0][0], counts_sorted[1][0])
    if counts_sorted[0][1] == 3 and counts_sorted[1][1] == 2: return (6, counts_sorted[0][0], counts_sorted[1][0])
    if is_flush: return (5, values)
    if is_straight: return (4, values)
    if counts_sorted[0][1] == 3: return (3, counts_sorted[0][0], [v for v in values if v != counts_sorted[0][0]])
    if counts_sorted[0][1] == 2 and counts_sorted[1][1] == 2: return (2, counts_sorted[0][0], counts_sorted[1][0], counts_sorted[2][0])
    if counts_sorted[0][1] == 2: return (1, counts_sorted[0][0], [v for v in values if v != counts_sorted[0][0]])
    
    return (0, values)

def evaluate_best_hand(hole_cards, community_cards):
    """Evaluates all 5-card combinations from the 7 available cards."""
    all_cards = hole_cards + community_cards
    best_score = (0,)
    for combo in itertools.combinations(all_cards, 5):
        score = evaluate_hand(list(combo))
        if score > best_score:
            best_score = score
    return best_score

def hand_name(score_tuple):
    names = ["High Card", "One Pair", "Two Pair", "Three of a Kind", 
             "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]
    return names[score_tuple[0]]

def print_separator():
    print("=" * 60)

def play_texas_holdem():
    print_separator()
    print("      🌟 🎰 LAS VEGAS TEXAS HOLD'EM POKER 🎰 🌟")
    print("            (1 Pemain vs 4 Bot + Dealer)")
    print_separator()
    money = 5000
    
    all_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta"]
    
    while money > 0:
        print(f"\n💵 Saldo chips kamu: ${money}")
        start = input("Tekan Enter untuk mulai ronde baru (atau ketik 'quit' untuk keluar)... ")
        if start.lower() == 'quit':
            break
            
        deck = Deck()
        pot = 0
        
        # Ante / Blinds (simplified as just an entry fee)
        ante = 50
        if money < ante:
            print("Chips kamu habis! Game Over.")
            break
            
        print(f"\n💳 Semua pemain membayar Blind (Ante): ${ante}")
        money -= ante
        active_bots = all_bots.copy()
        pot += ante * (len(active_bots) + 1)
        player_active = True
        
        print("🤵 Dealer mengocok kartu dan membagikan 2 Hole Cards...")
        time.sleep(1.5)
        
        player_hole = deck.draw(2)
        bot_holes = {bot: deck.draw(2) for bot in all_bots}
        community = []
        
        def bot_action(bot_name, current_to_call):
            nonlocal pot
            # Simple AI behavior: randomly call, check, raise, or fold.
            choices = ['call', 'call', 'call', 'raise', 'fold']
            if current_to_call == 0:
                choices = ['check', 'check', 'check', 'raise', 'fold']
                
            # Make bots slightly more likely to call/check than fold
            action = random.choice(choices)
            
            if action == 'fold':
                print(f"🤖 {bot_name} FOLD.")
                active_bots.remove(bot_name)
                return 0
            elif action == 'raise':
                raise_amt = random.choice([50, 100, 200])
                print(f"🤖 {bot_name} RAISE ${raise_amt}!")
                pot += raise_amt
                return raise_amt
            else: # call or check
                if current_to_call > 0:
                    print(f"🤖 {bot_name} CALL ${current_to_call}.")
                    pot += current_to_call
                else:
                    print(f"🤖 {bot_name} CHECK.")
                return 0

        def betting_round(stage_name):
            nonlocal money, pot, player_active
            print_separator()
            print(f"--- FASE: {stage_name.upper()} ---")
            print(f"Kartu kamu : [ {player_hole[0]} ] [ {player_hole[1]} ]")
            if community:
                print(f"Kartu Meja : " + " | ".join(str(c) for c in community))
            print(f"Total Pot  : ${pot} | Saldo Kamu: ${money}")
            print_separator()
            
            current_to_call = 0
            
            # Bot Turn
            for bot in active_bots.copy(): # Iterate a copy because we might remove a bot
                time.sleep(0.8)
                added_bet = bot_action(bot, current_to_call)
                if added_bet > 0:
                    current_to_call += added_bet
                    
            if not player_active:
                return
                
            # Player Turn
            time.sleep(1)
            print(f"\n🤵 Giliran kamu!")
            if current_to_call > 0:
                print(f"⚠️ Kamu harus CALL ${current_to_call} untuk lanjut, atau FOLD.")
                
            while True:
                action = input(f"Aksi (call / check / raise / all-in / fold): ").lower().strip()
                if action in ['fold', 'f']:
                    print("Kamu FOLD.")
                    player_active = False
                    break
                elif action in ['all-in', 'all in', 'allin', 'a']:
                    print(f"🔥 KAMU ALL-IN! Mempertaruhkan seluruh sisa uangmu sebesar ${money}! 🔥")
                    amt = money
                    money = 0
                    pot += amt
                    
                    added_raise = amt - current_to_call if amt > current_to_call else 0
                    
                    if added_raise > 0:
                        print("🤵 Dealer menunggu respons bot terhadap All-In kamu...")
                        time.sleep(1)
                        for bot in active_bots:
                            print(f"🤖 {bot} CALL tambahan All-In sebesar ${added_raise}.")
                            pot += added_raise
                    break
                elif action in ['call', 'c', '']:
                    if current_to_call > 0:
                        if money >= current_to_call:
                            money -= current_to_call
                            pot += current_to_call
                            print(f"Kamu CALL ${current_to_call}.")
                            break
                        else:
                            print(f"❌ Uang kamu tidak cukup untuk call ${current_to_call}. Kamu otomatis ALL-IN!")
                            pot += money
                            money = 0
                            break
                    else:
                        print("Kamu CHECK.")
                        break
                elif action in ['check']:
                    if current_to_call > 0:
                        print(f"❌ Tidak bisa check, ada yang RAISE. Kamu harus call ${current_to_call} atau fold.")
                    else:
                        print("Kamu CHECK.")
                        break
                elif action.startswith('raise') or action.startswith('r'):
                    try:
                        parts = action.split()
                        amt = int(parts[1]) if len(parts) > 1 else int(input("Raise berapa? $"))
                        if amt >= money:
                            print(f"🔥 RAISE kamu sama dengan/lebih dari sisa uangmu, otomatis jadi ALL-IN! 🔥")
                            amt = money
                            money = 0
                            pot += amt
                            
                            added_raise = amt - current_to_call if amt > current_to_call else 0
                            if added_raise > 0:
                                print("🤵 Dealer menunggu respons bot terhadap All-In kamu...")
                                time.sleep(1)
                                for bot in active_bots:
                                    print(f"🤖 {bot} CALL tambahan All-In sebesar ${added_raise}.")
                                    pot += added_raise
                            break
                        else:
                            print(f"Kamu RAISE ${amt}.")
                            money -= (current_to_call + amt)
                            pot += (current_to_call + amt)
                            
                            # Simulate active bots calling your raise
                            print("🤵 Dealer menunggu respons bot terhadap raise kamu...")
                            time.sleep(1)
                            for bot in active_bots:
                                print(f"🤖 {bot} CALL ${amt}.")
                                pot += amt
                            break
                    except ValueError:
                        print("❌ Input tidak valid.")
                else:
                    print("❌ Perintah tidak dikenali.")
            
        # 1. Pre-flop
        betting_round("Pre-Flop")
        
        # 2. Flop (3 cards)
        if active_bots or player_active:
            print("\n🤵 Dealer membuka 3 kartu Flop...")
            time.sleep(1)
            community.extend(deck.draw(3))
            betting_round("Flop")
            
        # 3. Turn (1 card)
        if active_bots or player_active:
            print("\n🤵 Dealer membuka 1 kartu Turn...")
            time.sleep(1)
            community.append(deck.draw(1))
            betting_round("Turn")
            
        # 4. River (1 card)
        if active_bots or player_active:
            print("\n🤵 Dealer membuka 1 kartu River...")
            time.sleep(1)
            community.append(deck.draw(1))
            betting_round("River")
            
        # Showdown
        print_separator()
        print("🌟 SHOWDOWN! 🌟")
        print_separator()
        print(f"Kartu Meja : " + " | ".join(str(c) for c in community))
        print()
        
        best_scores = {}
        if player_active:
            best_scores["Kamu"] = evaluate_best_hand(player_hole, community)
            print(f"🧑 KAMU      : [ {player_hole[0]} ] [ {player_hole[1]} ]  ✨ {hand_name(best_scores['Kamu'])} ✨")
            
        for bot in active_bots:
            best_scores[bot] = evaluate_best_hand(bot_holes[bot], community)
            print(f"🤖 {bot.upper():<10}: [ {bot_holes[bot][0]} ] [ {bot_holes[bot][1]} ]  ✨ {hand_name(best_scores[bot])} ✨")
            
        time.sleep(2)
        
        if not best_scores:
             print("\nSemua pemain FOLD. Tidak ada pemenang.")
             continue
             
        # Find Winner
        ranked = sorted(best_scores.items(), key=lambda x: x[1], reverse=True)
        winner_score = ranked[0][1]
        winners = [name for name, score in ranked if score == winner_score]
        
        print("\n🤵 Dealer mengumumkan:")
        time.sleep(1)
        if len(winners) > 1:
            print(f"   SERI antara {', '.join(winners)}!")
            if "Kamu" in winners:
                win_amount = pot // len(winners)
                print(f"🤝 Kamu berbagi pot dan mendapatkan ${win_amount}!")
                money += win_amount
            else:
                print(f"💀 Pot sebesar ${pot} dibagi antara bot. Kamu tidak dapat apa-apa.")
        else:
            print(f"   {winners[0].upper()} MENANG dengan kombinasi {hand_name(winner_score)}!")
            if winners[0] == "Kamu":
                print(f"🏆 SELAMAT! Kamu mengambil semua pot sebesar ${pot}! 🏆")
                money += pot
            else:
                print(f"💀 YAHH.. Pot sebesar ${pot} diambil oleh {winners[0]}. 💀")
                
    print("\nGame Over! Kamu kehabisan uang atau memutuskan meninggalkan meja kasino. 👋")

if __name__ == '__main__':
    try:
        play_texas_holdem()
    except KeyboardInterrupt:
        print("\n\nGame dihentikan. Sampai jumpa di meja berikutnya!")
