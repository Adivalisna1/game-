import random
import itertools
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'poker-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

SUITS = ['♥️', '♦️', '♣️', '♠️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]
    def to_dict(self):
        return {'rank': self.rank, 'suit': self.suit, 'color': 'red' if self.suit in ['♥️', '♦️'] else 'black'}

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for r in RANKS for s in SUITS]
        random.shuffle(self.cards)
    def draw(self, n=1):
        drawn = [self.cards.pop() for _ in range(n) if self.cards]
        return drawn[0] if n == 1 else drawn

def evaluate_hand(hand):
    values = sorted([card.value for card in hand], reverse=True)
    suits = [card.suit for card in hand]
    is_flush = len(set(suits)) == 1
    is_straight = False
    if len(set(values)) == 5 and values[0] - values[-1] == 4:
        is_straight = True
    elif values == [14, 5, 4, 3, 2]:
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
    all_cards = hole_cards + community_cards
    best_score = (0,)
    for combo in itertools.combinations(all_cards, 5):
        score = evaluate_hand(list(combo))
        if score > best_score:
            best_score = score
    return best_score

class GameState:
    def __init__(self):
        self.players = {} 
        self.sids = [] 
        self.state = 'waiting' 
        self.phase = 'preflop' 
        self.community_cards = []
        self.deck = None
        self.pot = 0
        self.current_turn_idx = 0
        self.highest_bet = 0
        self.dealer_idx = 0
        
    def add_player(self, sid, name, is_bot=False):
        if sid not in self.players:
            self.players[sid] = {'name': name, 'money': 5000, 'hole_cards': [], 'bet': 0, 'status': 'waiting', 'is_bot': is_bot}
            self.sids.append(sid)
            
    def remove_player(self, sid):
        if sid in self.players:
            del self.players[sid]
            self.sids.remove(sid)
            
    def start_hand(self):
        if len(self.players) < 2:
            return False
            
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.highest_bet = 50 
        self.state = 'playing'
        self.phase = 'preflop'
        
        self.dealer_idx = (self.dealer_idx + 1) % len(self.sids)
        
        for sid in self.sids:
            p = self.players[sid]
            if p['money'] > 0:
                p['status'] = 'active'
                p['hole_cards'] = self.deck.draw(2)
                ante = min(50, p['money'])
                p['money'] -= ante
                p['bet'] = ante
                self.pot += ante
            else:
                p['status'] = 'out'
                
        self.current_turn_idx = (self.dealer_idx + 1) % len(self.sids)
        self.skip_inactive()
        return True
        
    def skip_inactive(self):
        start_idx = self.current_turn_idx
        while True:
            if not self.sids: break
            sid = self.sids[self.current_turn_idx]
            if self.players[sid]['status'] == 'active':
                break
            self.current_turn_idx = (self.current_turn_idx + 1) % len(self.sids)
            if self.current_turn_idx == start_idx:
                self.next_phase()
                break

    def get_public_state(self):
        return {
            'state': self.state,
            'phase': self.phase,
            'community_cards': [c.to_dict() for c in self.community_cards],
            'pot': self.pot,
            'highest_bet': self.highest_bet,
            'current_turn_sid': self.sids[self.current_turn_idx] if self.sids else None,
            'players': [
                {
                    'sid': sid,
                    'name': self.players[sid]['name'],
                    'money': self.players[sid]['money'],
                    'bet': self.players[sid]['bet'],
                    'status': self.players[sid]['status'],
                    'hole_cards': [c.to_dict() for c in self.players[sid]['hole_cards']] if self.state == 'showdown' and self.players[sid]['status'] in ['active', 'all-in'] else []
                } for sid in self.sids
            ]
        }
        
    def next_phase(self):
        active = [sid for sid in self.sids if self.players[sid]['status'] == 'active']
        all_in = [sid for sid in self.sids if self.players[sid]['status'] == 'all-in']
        
        if len(active) + len(all_in) <= 1 or len(active) == 0:
            self.showdown()
            return
            
        for sid in self.sids:
            if self.players[sid]['status'] == 'active':
                self.players[sid]['bet'] = 0
        self.highest_bet = 0
        self.current_turn_idx = (self.dealer_idx + 1) % len(self.sids)
        self.skip_inactive()

        if self.phase == 'preflop':
            self.phase = 'flop'
            self.community_cards.extend(self.deck.draw(3))
        elif self.phase == 'flop':
            self.phase = 'turn'
            self.community_cards.append(self.deck.draw(1))
        elif self.phase == 'turn':
            self.phase = 'river'
            self.community_cards.append(self.deck.draw(1))
        elif self.phase == 'river':
            self.showdown()

    def showdown(self):
        self.state = 'showdown'
        while len(self.community_cards) < 5:
            self.community_cards.append(self.deck.draw(1))
            
        best_score = (-1,)
        winners = []
        for sid in self.sids:
            p = self.players[sid]
            if p['status'] in ['active', 'all-in']:
                score = evaluate_best_hand(p['hole_cards'], self.community_cards)
                if score > best_score:
                    best_score = score
                    winners = [sid]
                elif score == best_score:
                    winners.append(sid)
                    
        if winners:
            win_amount = self.pot // len(winners)
            for sid in winners:
                self.players[sid]['money'] += win_amount
                
        self.pot = 0

game = GameState()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_solo')
def handle_join_solo(data):
    global game
    game = GameState() # Reset game for solo
    game.add_player(request.sid, data['name'][:12])
    game.add_player('bot_1', 'Bot Alpha', is_bot=True)
    game.add_player('bot_2', 'Bot Bravo', is_bot=True)
    game.add_player('bot_3', 'Bot Charlie', is_bot=True)
    game.add_player('bot_4', 'Bot Delta', is_bot=True)
    emit('update', game.get_public_state(), broadcast=True)

@socketio.on('join_lan')
def handle_join_lan(data):
    game.add_player(request.sid, data['name'][:12])
    emit('update', game.get_public_state(), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    game.remove_player(request.sid)
    emit('update', game.get_public_state(), broadcast=True)

def check_bot_turn():
    if game.state != 'playing': return
    if not game.sids: return
    current_sid = game.sids[game.current_turn_idx]
    p = game.players[current_sid]
    if p.get('is_bot'):
        socketio.start_background_task(bot_act, current_sid)

def bot_act(sid):
    socketio.sleep(1.5) # Simulate thinking
    if game.state != 'playing' or game.sids[game.current_turn_idx] != sid:
        return
        
    p = game.players[sid]
    to_call = game.highest_bet - p['bet']
    
    choices = ['call', 'call', 'call', 'raise', 'fold']
    if to_call == 0:
        choices = ['check', 'check', 'check', 'raise', 'fold']
        
    action = random.choice(choices)
    amt = 0
    if action == 'raise':
        amt = random.choice([50, 100, 200])
        
    process_action(sid, action, amt)

def process_action(sid, action, amount=0):
    if game.state != 'playing' or not game.sids or game.sids[game.current_turn_idx] != sid:
        return
        
    p = game.players[sid]
    to_call = game.highest_bet - p['bet']
    
    if action == 'fold':
        p['status'] = 'folded'
    elif action in ['call', 'check']:
        if p['money'] <= to_call:
            game.pot += p['money']
            p['bet'] += p['money']
            p['money'] = 0
            p['status'] = 'all-in'
            if p['bet'] > game.highest_bet: game.highest_bet = p['bet']
        else:
            p['money'] -= to_call
            game.pot += to_call
            p['bet'] += to_call
    elif action == 'raise':
        total_needed = to_call + amount
        if p['money'] <= total_needed:
            game.pot += p['money']
            p['bet'] += p['money']
            p['money'] = 0
            p['status'] = 'all-in'
            if p['bet'] > game.highest_bet: game.highest_bet = p['bet']
        else:
            p['money'] -= total_needed
            game.pot += total_needed
            p['bet'] += total_needed
            game.highest_bet = p['bet']
            
    active_players = [s for s in game.sids if game.players[s]['status'] == 'active']
    
    round_over = True
    for s in active_players:
        if game.players[s]['bet'] < game.highest_bet:
            round_over = False
            break
            
    if round_over and (action != 'fold' or len(active_players) <= 1):
        game.next_phase()
    else:
        game.current_turn_idx = (game.current_turn_idx + 1) % len(game.sids)
        game.skip_inactive()
        
    socketio.emit('update', game.get_public_state())
    check_bot_turn()

@socketio.on('start')
def handle_start():
    if game.state in ['waiting', 'showdown']:
        active_count = sum(1 for p in game.players.values() if p['money'] > 0)
        if len(game.players) >= 2 and active_count < 2:
            socketio.emit('alert', {'message': '🏆 GAME OVER! 🏆\nSemua chips udah ludes! Refresh halaman untuk main lagi.'})
            return
            
        success = game.start_hand()
        if success:
            emit('update', game.get_public_state(), broadcast=True)
            for sid in game.sids:
                if not game.players[sid].get('is_bot'):
                    emit('private_data', {'hole_cards': [c.to_dict() for c in game.players[sid]['hole_cards']]}, room=sid)
            check_bot_turn()

@socketio.on('action')
def handle_action(data):
    process_action(request.sid, data['action'], int(data.get('amount', 0)))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
