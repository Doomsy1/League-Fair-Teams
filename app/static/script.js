// app/static/script.js

document.addEventListener('DOMContentLoaded', () => {
    const team1List = document.getElementById('list1');
    const team2List = document.getElementById('list2');
    const summonerForm = document.getElementById('summoner-form');
    const addSummonerButton = document.getElementById('add-summoner-button');
    const buttonText = document.getElementById('button-text');
    const buttonSpinner = document.getElementById('button-spinner');
    const gamesSlider = document.getElementById('games-slider');
    const sliderTooltip = document.getElementById('slider-tooltip');

    // Load teams from localStorage
    let teams = JSON.parse(localStorage.getItem('teams')) || { team1: [], team2: [] };

    // Render teams
    function renderTeams() {
        team1List.innerHTML = '';
        team2List.innerHTML = '';

        teams.team1.forEach(summoner => {
            const playerItem = createPlayerItem(summoner);
            team1List.appendChild(playerItem);
        });

        teams.team2.forEach(summoner => {
            const playerItem = createPlayerItem(summoner);
            team2List.appendChild(playerItem);
        });
    }

    // Create player item element
    function createPlayerItem(summoner) {
        const li = document.createElement('li');
        li.classList.add('player-item');
        li.setAttribute('data-name', `${summoner.game_name}#${summoner.tag_line}`);

        const playerIcon = document.createElement('div');
        playerIcon.classList.add('player-icon');
        const img = document.createElement('img');
        img.src = summoner.icon_url;
        img.alt = 'Icon';
        playerIcon.appendChild(img);

        const playerInfo = document.createElement('div');
        playerInfo.classList.add('player-info');

        const playerHeader = document.createElement('div');
        playerHeader.classList.add('player-header');
        const playerName = document.createElement('span');
        playerName.classList.add('player-name');
        playerName.textContent = summoner.game_name;
        playerHeader.appendChild(playerName);

        const playerRankContainer = document.createElement('div');
        playerRankContainer.classList.add('player-rank-container');
        const playerRank = document.createElement('span');
        playerRank.classList.add('player-rank', summoner.tier.toLowerCase());
        playerRank.textContent = summoner.rank;
        const rankImg = document.createElement('img');
        rankImg.src = `/static/images/ranks/${summoner.tier.toLowerCase()}.webp`;
        rankImg.alt = `${summoner.tier} Rank`;
        rankImg.classList.add('rank-image');
        playerRank.appendChild(rankImg);
        playerRankContainer.appendChild(playerRank);

        const actionButtons = document.createElement('div');
        actionButtons.classList.add('action-buttons');

        const moveButton = document.createElement('button');
        moveButton.classList.add('move-button');
        moveButton.textContent = '⇄';
        moveButton.addEventListener('click', moveSummoner);

        const removeButton = document.createElement('button');
        removeButton.classList.add('remove-button');
        removeButton.textContent = '✖';
        removeButton.addEventListener('click', removeSummoner);

        actionButtons.appendChild(moveButton);
        actionButtons.appendChild(removeButton);

        playerInfo.appendChild(playerHeader);
        playerInfo.appendChild(playerRankContainer);
        playerInfo.appendChild(actionButtons);

        li.appendChild(playerIcon);
        li.appendChild(playerInfo);

        return li;
    }

    // Initialize Sortable for Team 1
    new Sortable(team1List, {
        group: 'teams',
        animation: 150,
        onAdd: function (evt) {
            handleTeamChange(evt, 'team1');
        }
    });

    // Initialize Sortable for Team 2
    new Sortable(team2List, {
        group: 'teams',
        animation: 150,
        onAdd: function (evt) {
            handleTeamChange(evt, 'team2');
        }
    });

    // Function to handle team changes via drag and drop
    function handleTeamChange(evt, newTeam) {
        const summonerFullName = evt.item.getAttribute('data-name');
        updateSummonerTeam(summonerFullName, newTeam);
    }

    // Function to add summoner
    summonerForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const gameNameInput = document.getElementById('game-name');
        const tagLineInput = document.getElementById('tag-line');
        const gameName = gameNameInput.value.trim();
        const tagLine = tagLineInput.value.trim();

        if (!gameName || !tagLine) {
            alert('Both Game Name and Tag Line are required.');
            return;
        }

        // Check if summoner already exists
        if (teams.team1.concat(teams.team2).some(s => s.game_name === gameName && s.tag_line === tagLine)) {
            alert('Summoner already exists.');
            return;
        }

        // Determine which team to assign
        let assignedTeam = '';
        if (teams.team1.length < 5) {
            assignedTeam = 'team1';
        } else if (teams.team2.length < 5) {
            assignedTeam = 'team2';
        } else {
            alert('Both teams are full. Please remove a player before adding a new one.');
            return;
        }

        // Show loading spinner and disable button
        showSpinner();
        addSummonerButton.disabled = true;

        // Fetch summoner data from server
        fetch('/get_summoner_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ game_name: gameName, tag_line: tagLine })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner and enable button
            hideSpinner();
            addSummonerButton.disabled = false;

            if (data.status === 'success') {
                const summoner = data.summoner;
                summoner.team = assignedTeam;
                teams[assignedTeam].push(summoner);
                localStorage.setItem('teams', JSON.stringify(teams));
                renderTeams();
                attachActionListeners();
            } else {
                alert(data.message || 'Failed to add summoner.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the summoner.');
            // Hide loading spinner and enable button
            hideSpinner();
            addSummonerButton.disabled = false;
        });

        // Clear input fields
        gameNameInput.value = '';
        tagLineInput.value = '';
    });

    // Function to remove summoner
    function removeSummoner(e) {
        const button = e.target;
        const playerItem = button.closest('.player-item');
        const summonerFullName = playerItem.getAttribute('data-name');
        const [game_name, tag_line] = summonerFullName.split('#');

        // Remove summoner from teams
        teams.team1 = teams.team1.filter(s => !(s.game_name === game_name && s.tag_line === tag_line));
        teams.team2 = teams.team2.filter(s => !(s.game_name === game_name && s.tag_line === tag_line));
        localStorage.setItem('teams', JSON.stringify(teams));
        renderTeams();
        attachActionListeners();
    }

    // Function to move summoner to the other team via Move button
    function moveSummoner(e) {
        const button = e.target;
        const playerItem = button.closest('.player-item');
        const summonerFullName = playerItem.getAttribute('data-name');
        const [game_name, tag_line] = summonerFullName.split('#');
        const currentTeam = playerItem.closest('.team').id;
        const newTeam = currentTeam === 'team1' ? 'team2' : 'team1';

        if (teams[newTeam].length >= 5) {
            alert(`${newTeam === 'team1' ? 'Team 1' : 'Team 2'} is full. Please remove a player before moving another one.`);
            return;
        }

        // Move summoner to the other team
        const summonerIndex = teams[currentTeam].findIndex(s => s.game_name === game_name && s.tag_line === tag_line);
        if (summonerIndex !== -1) {
            const [summoner] = teams[currentTeam].splice(summonerIndex, 1);
            summoner.team = newTeam;
            teams[newTeam].push(summoner);
            localStorage.setItem('teams', JSON.stringify(teams));
            renderTeams();
            attachActionListeners();
        }
    }

    // Function to update summoner team via drag and drop
    function updateSummonerTeam(summonerFullName, newTeam) {
        const [game_name, tag_line] = summonerFullName.split('#');
        const oldTeam = newTeam === 'team1' ? 'team2' : 'team1';

        if (teams[newTeam].length >= 5) {
            alert(`${newTeam === 'team1' ? 'Team 1' : 'Team 2'} is full. Please remove a player before moving another one.`);
            renderTeams();
            attachActionListeners();
            return;
        }

        // Move summoner to the new team
        const summonerIndex = teams[oldTeam].findIndex(s => s.game_name === game_name && s.tag_line === tag_line);
        if (summonerIndex !== -1) {
            const [summoner] = teams[oldTeam].splice(summonerIndex, 1);
            summoner.team = newTeam;
            teams[newTeam].push(summoner);
            localStorage.setItem('teams', JSON.stringify(teams));
            renderTeams();
            attachActionListeners();
        }
    }

    // Attach removeSummoner and moveSummoner event listeners to all existing buttons
    function attachActionListeners() {
        const removeButtons = document.querySelectorAll('.remove-button');
        removeButtons.forEach(button => {
            button.removeEventListener('click', removeSummoner);
            button.addEventListener('click', removeSummoner);
        });

        const moveButtons = document.querySelectorAll('.move-button');
        moveButtons.forEach(button => {
            button.removeEventListener('click', moveSummoner);
            button.addEventListener('click', moveSummoner);
        });
    }

    // Attach event listener to the Balance Teams button
    const balanceButton = document.getElementById('balance-teams-button');
    balanceButton.addEventListener('click', balanceTeams);

    // Function to balance teams based on MMR
    function balanceTeams() {
        const allSummoners = teams.team1.concat(teams.team2);
        // Sort summoners by MMR descending
        allSummoners.sort((a, b) => b.mmr - a.mmr);

        teams.team1 = [];
        teams.team2 = [];
        let totalMMRTeam1 = 0;
        let totalMMRTeam2 = 0;

        allSummoners.forEach(summoner => {
            if (teams.team1.length < 5 && (totalMMRTeam1 <= totalMMRTeam2 || teams.team2.length >= 5)) {
                summoner.team = 'team1';
                teams.team1.push(summoner);
                totalMMRTeam1 += summoner.mmr;
            } else if (teams.team2.length < 5) {
                summoner.team = 'team2';
                teams.team2.push(summoner);
                totalMMRTeam2 += summoner.mmr;
            }
        });

        localStorage.setItem('teams', JSON.stringify(teams));
        renderTeams();
        attachActionListeners();
    }

    // Attach event listener to the Clear All Players button
    const clearPlayersButton = document.getElementById('clear-players-button');
    clearPlayersButton.addEventListener('click', clearPlayers);

    function clearPlayers() {
        teams = { team1: [], team2: [] };
        localStorage.removeItem('teams');
        renderTeams();
        attachActionListeners();
    }

    // Slider for Games to Analyze with Tooltip
    gamesSlider.addEventListener('input', () => {
        const value = gamesSlider.value;
        sliderTooltip.textContent = value;

        // Calculate the position of the tooltip
        const sliderRect = gamesSlider.getBoundingClientRect();
        const tooltipWidth = sliderTooltip.offsetWidth;
        const sliderWidth = gamesSlider.offsetWidth;
        const thumbPosition = (value - gamesSlider.min) / (gamesSlider.max - gamesSlider.min);
        const tooltipX = thumbPosition * sliderWidth;

        // Position the tooltip
        sliderTooltip.style.left = `${tooltipX}px`;
    });

    gamesSlider.addEventListener('mousedown', () => {
        sliderTooltip.style.display = 'block';
    });

    gamesSlider.addEventListener('mouseup', () => {
        sliderTooltip.style.display = 'none';
    });

    gamesSlider.addEventListener('touchstart', () => {
        sliderTooltip.style.display = 'block';
    });

    gamesSlider.addEventListener('touchend', () => {
        sliderTooltip.style.display = 'none';
    });

    // Function to show spinner next to the button
    function showSpinner() {
        buttonSpinner.style.visibility = 'visible';
    }

    // Function to hide spinner next to the button
    function hideSpinner() {
        buttonSpinner.style.visibility = 'hidden';
    }

    // Initial render
    renderTeams();
    attachActionListeners();
});
