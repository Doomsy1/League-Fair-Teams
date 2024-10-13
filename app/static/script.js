// app/static/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Sortable for Team 1
    new Sortable(document.getElementById('list1'), {
        group: 'teams', // Set both lists to the same group for inter-list drag
        animation: 150,  // Animation speed in ms
        onAdd: function (evt) {
            handleTeamChange(evt, 'team1');
        },
        onEnd: function (evt) {
            // Finalize team change after drag ends
        }
    });

    // Initialize Sortable for Team 2
    new Sortable(document.getElementById('list2'), {
        group: 'teams', // Set both lists to the same group for inter-list drag
        animation: 150,  // Animation speed in ms
        onAdd: function (evt) {
            handleTeamChange(evt, 'team2');
        },
        onEnd: function (evt) {
            // Finalize team change after drag ends
        }
    });

    // Function to handle team changes
    function handleTeamChange(evt, newTeam) {
        const summonerNameWithTag = evt.item.querySelector('.player-name').innerText.trim().split(' (')[0];
        const [gameName, tagLine] = summonerNameWithTag.split('#');
        const summonerFullName = `${gameName}#${tagLine}`;
        updateSummonerTeam(summonerFullName, newTeam);
    }

    // Function to remove summoner
    function removeSummoner(e) {
        const button = e.target;
        const summonerFullName = button.getAttribute('data-name');
        const playerItem = button.closest('.player-item');

        // Send AJAX request to remove the summoner
        fetch('/remove_summoner', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ summoner_name: summonerFullName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Remove the element from the DOM
                playerItem.remove();
            } else {
                alert(data.message || 'Failed to remove summoner.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while removing the summoner.');
        });
    }

    // Function to update summoner team
    function updateSummonerTeam(summonerFullName, newTeam) {
        // Send AJAX request to update the summoner's team
        fetch('/update_team', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ summoner_name: summonerFullName, new_team: newTeam })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                alert(data.message || 'Failed to update team.');
                // Revert the drag action by reloading the page
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the team.');
            // Revert the drag action by reloading the page
            location.reload();
        });
    }

    // Attach removeSummoner event listeners to all existing remove buttons
    const removeButtons = document.querySelectorAll('.remove-button');
    removeButtons.forEach(button => {
        button.addEventListener('click', removeSummoner);
    });

    // Attach event listener to the Balance Teams button
    const balanceButton = document.getElementById('balance-teams-button');
    balanceButton.addEventListener('click', balanceTeams);

    function balanceTeams() {
        fetch('/balance_teams', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Reload the page to reflect the new team assignments
                location.reload();
            } else {
                alert(data.message || 'Failed to balance teams.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while balancing teams.');
        });
    }
});
