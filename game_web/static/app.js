const socket = io();

const loginScreen = document.getElementById('login-screen');
const gameScreen = document.getElementById('game-screen');
const joinSoloBtn = document.getElementById('join-solo-btn');
const joinLanBtn = document.getElementById('join-lan-btn');
const usernameInput = document.getElementById('username');

let mySid = null;
let currentGameState = null;

// Login Logic
joinSoloBtn.addEventListener('click', () => {
    const name = usernameInput.value.trim() || "Player";
    socket.emit('join_solo', { name });
    loginScreen.classList.remove('active');
    gameScreen.classList.add('active');
});

joinLanBtn.addEventListener('click', () => {
    const name = usernameInput.value.trim() || "Player";
    socket.emit('join_lan', { name });
    loginScreen.classList.remove('active');
    gameScreen.classList.add('active');
});

socket.on('connect', () => {
    mySid = socket.id;
});

// Update state from server
socket.on('update', (state) => {
    currentGameState = state;
    renderTable();
    updateControls();
});

// Receive my private hole cards
socket.on('private_data', (data) => {
    renderMyCards(data.hole_cards);
});

socket.on('alert', (data) => {
    alert(data.message);
});

function createCardHTML(card) {
    if (!card) return `<div class="playing-card back"></div>`;
    return `<div class="playing-card face ${card.color}">
                <div class="rank">${card.rank}</div>
                <div class="suit">${card.suit}</div>
            </div>`;
}

function renderTable() {
    if(!currentGameState) return;

    // Community cards
    const commContainer = document.getElementById('community-cards');
    commContainer.innerHTML = '';
    currentGameState.community_cards.forEach(card => {
        commContainer.innerHTML += createCardHTML(card);
    });

    // Pot and Phase
    document.getElementById('pot-amount').textContent = `$${currentGameState.pot}`;
    document.getElementById('phase-badge').textContent = currentGameState.phase.toUpperCase();
    
    // Opponents rendering
    const playersContainer = document.getElementById('players-list');
    playersContainer.innerHTML = '';
    
    currentGameState.players.forEach(p => {
        if (p.sid === mySid) {
            document.getElementById('my-name').textContent = p.name;
            document.getElementById('my-money').textContent = `$${p.money} (Bet: $${p.bet})`;
            if (currentGameState.state === 'showdown' && p.hole_cards.length > 0) {
                 renderMyCards(p.hole_cards);
            }
            if (currentGameState.state === 'waiting') {
                document.getElementById('my-cards').innerHTML = '';
            }
            return;
        }
        
        const isTurn = currentGameState.current_turn_sid === p.sid ? 'turn-active' : '';
        let cardsHtml = '';
        if (currentGameState.state === 'showdown' && p.hole_cards.length > 0) {
             cardsHtml = p.hole_cards.map(c => createCardHTML(c)).join('');
        } else if (p.status === 'active' || p.status === 'all-in') {
             cardsHtml = createCardHTML(null) + createCardHTML(null);
        }
        
        playersContainer.innerHTML += `
            <div class="player-card glass ${isTurn}">
                <div class="p-name">${p.name} ${p.status === 'all-in' ? '<span style="color:var(--danger)">ALL-IN</span>' : ''}</div>
                <div class="p-money">$${p.money}</div>
                <div class="p-bet">Bet: $${p.bet}</div>
                <div class="p-cards">${cardsHtml}</div>
                <div class="p-status">${p.status.toUpperCase()}</div>
            </div>
        `;
    });
}

function renderMyCards(cards) {
    const container = document.getElementById('my-cards');
    container.innerHTML = cards.map(c => createCardHTML(c)).join('');
}

function updateControls() {
    const controls = document.getElementById('action-controls');
    const startBtn = document.getElementById('btn-start');
    
    if (!currentGameState) return;
    
    if (currentGameState.state === 'waiting' || currentGameState.state === 'showdown') {
        startBtn.classList.remove('hidden');
        controls.classList.add('hidden');
        return;
    }
    
    startBtn.classList.add('hidden');
    
    // Check if it's my turn
    if (currentGameState.current_turn_sid === mySid) {
        controls.classList.remove('hidden');
        
        const me = currentGameState.players.find(p => p.sid === mySid);
        const toCall = currentGameState.highest_bet - me.bet;
        document.getElementById('to-call-amt').textContent = toCall;
        
        if (toCall > 0) {
            document.getElementById('btn-check').classList.add('hidden');
            document.getElementById('btn-call').classList.remove('hidden');
            document.getElementById('btn-call').textContent = `Call $${toCall}`;
        } else {
            document.getElementById('btn-check').classList.remove('hidden');
            document.getElementById('btn-call').classList.add('hidden');
        }
    } else {
        controls.classList.add('hidden');
    }
}

// Action Listeners
document.getElementById('btn-start').onclick = () => socket.emit('start');
document.getElementById('btn-fold').onclick = () => socket.emit('action', { action: 'fold' });
document.getElementById('btn-check').onclick = () => socket.emit('action', { action: 'call' });
document.getElementById('btn-call').onclick = () => socket.emit('action', { action: 'call' });
document.getElementById('btn-raise').onclick = () => {
    const amt = parseInt(document.getElementById('raise-input').value);
    if (amt && amt > 0) {
        socket.emit('action', { action: 'raise', amount: amt });
        document.getElementById('raise-input').value = '';
    }
};
document.getElementById('btn-allin').onclick = () => {
    const me = currentGameState.players.find(p => p.sid === mySid);
    socket.emit('action', { action: 'raise', amount: me.money });
};
