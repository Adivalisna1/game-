import random
import time

SUITS = ['♥️ Hearts', '♦️ Diamonds', '♣️ Clubs', '♠️ Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]
        
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
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
    
    if is_flush and is_straight:
        return (8, values)
    if counts_sorted[0][1] == 4:
        return (7, counts_sorted[0][0], counts_sorted[1][0])
    if counts_sorted[0][1] == 3 and counts_sorted[1][1] == 2:
        return (6, counts_sorted[0][0], counts_sorted[1][0])
    if is_flush:
        return (5, values)
    if is_straight:
        return (4, values)
    if counts_sorted[0][1] == 3:
        return (3, counts_sorted[0][0], [v for v in values if v != counts_sorted[0][0]])
    if counts_sorted[0][1] == 2 and counts_sorted[1][1] == 2:
        return (2, counts_sorted[0][0], counts_sorted[1][0], counts_sorted[2][0])
    if counts_sorted[0][1] == 2:
        return (1, counts_sorted[0][0], [v for v in values if v != counts_sorted[0][0]])
    
    return (0, values)

def hand_name(score_tuple):
    names = ["High Card", "One Pair", "Two Pair", "Three of a Kind", 
             "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]
    return names[score_tuple[0]]

def print_separator():
    print("=" * 40)

def play_five_card_draw():
    print_separator()
    print("♠️ ♥️  TERMINAL POKER (5-CARD DRAW) ♦️ ♣️")
    print_separator()
    money = 1000
    
    while money > 0:
        print(f"\n💰 Saldo kamu: ${money}")
        bet = input("Pasang taruhan (atau ketik 'quit' untuk keluar): ")
        
        if bet.lower() == 'quit':
            break
            
        try:
            bet = int(bet)
            if bet > money or bet <= 0:
                print("❌ Jumlah taruhan tidak valid.")
                continue
        except ValueError:
            print("❌ Masukkan angka yang valid.")
            continue
            
        deck = Deck()
        player_hand = deck.draw(5)
        bot_hand = deck.draw(5)
        
        print("\n🃏 Membagikan kartu...")
        time.sleep(1)
        
        print("\nKartu kamu:")
        for i, card in enumerate(player_hand):
            print(f"[{i+1}] {card}")
            
        discard = input("\nMasukkan nomor kartu yang ingin ditukar, pisahkan dengan spasi (contoh: '1 3 4').\nAtau tekan Enter jika tidak ingin menukar kartu: ")
        
        if discard.strip():
            try:
                indices = [int(x) - 1 for x in discard.split()]
                # Sort descending so popping doesn't shift the remaining indices
                for i in sorted(indices, reverse=True):
                    if 0 <= i < 5:
                        player_hand.pop(i)
                        player_hand.append(deck.draw(1))
            except:
                print("⚠️ Input tidak valid, tidak ada kartu yang ditukar.")
                
        print("\nKartu akhir kamu:")
        for card in player_hand:
            print(f" - {card}")
            
        player_score = evaluate_hand(player_hand)
        bot_score = evaluate_hand(bot_hand)
        
        print(f"\nKamu mendapat: ✨ {hand_name(player_score)} ✨")
        time.sleep(1)
        
        print("\n🤖 Kartu Bot:")
        for card in bot_hand:
            print(f" - {card}")
        print(f"Bot mendapat: {hand_name(bot_score)}")
        
        time.sleep(1)
        print_separator()
        if player_score > bot_score:
            print("🏆 KAMU MENANG! 🏆")
            money += bet
        elif player_score < bot_score:
            print("💀 KAMU KALAH! 💀")
            money -= bet
        else:
            print("🤝 SERI! (TIE) 🤝")
        print_separator()
            
    print("\nGame Over! Terima kasih sudah bermain. 👋")

if __name__ == '__main__':
    try:
        play_five_card_draw()
    except KeyboardInterrupt:
        print("\nGame dihentikan.")
