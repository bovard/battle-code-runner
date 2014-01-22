var fs = require('fs');
var request = require('request');

var file = fs.readFileSync('output.txt', 'utf-8');

var lines = file.split('\n');


function run() {
    var line = lines.shift();
    var entries = line.split(' ');
    var map = entries[0];
    var teams = entries[1].split('/');
    var teamA = teams[0].slice(1, teams[0].length);
    var teamB = teams[1].slice(0, teams[1].length - 1);
    var winner = entries[2];
    var round = entries[3];

    console.log(teamA, teamB, map);
    request.post(
        {
            uri: 'http://localhost:9080/game/',
            qs: {
                map: map,
                teamA: teamA,
                teamB: teamB,
                winner: winner,
                round: round
            }
        }, function(error, response, body) {
            //console.log(error, response, body);
        }
    );

    if (lines.length > 0) {
        setTimeout(run, 500);
    }
}


/*
for (var i = 0; i < lines.length; i++) {
    var entries = lines[i].split(' ');
    var map = entries[0];
    var teams = entries[1].split('/');
    var teamA = teams[0].slice(1, teams[0].length);
    var teamB = teams[1].slice(0, teams[1].length - 1);
    var winner = entries[2];
    var round = entries[3];
    console.log(map, teamA, teamB, winner, round);
}
*/

run();
