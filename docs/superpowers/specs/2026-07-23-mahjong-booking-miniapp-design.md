# Mahjong Booking Miniapp Design

## Overview

Build a WeChat-style miniapp prototype for private friend-group mahjong sessions. The product helps a small group quickly organize a table, track lightweight match results, and keep a playful leaderboard that makes people want to open the app again.

This first version is for friend games only. It does not include commercial room booking, venue inventory, payments, tournament administration, or detailed hand-by-hand scoring.

## Goals

- Let a group member create a mahjong session in under one minute.
- Make the next session status obvious: time, location, confirmed players, and missing seats.
- Let players join, cancel, or enter a waitlist with minimal friction.
- Record post-game results at the whole-session level.
- Automatically update win rate, activity, streak, no-show count, and leaderboard positions.
- Keep the tone social and lightly competitive, not overly professional.

## Users

- Organizer: creates sessions, edits session details, records results, and can mark no-shows.
- Player: joins or cancels sessions, confirms submitted results, and views rankings.
- Group member: views upcoming games and leaderboard even when not joining.

## Navigation

The first version uses five bottom tabs:

- Home: next session status, registration progress, ranking highlights, and recent activity.
- Booking: create and manage sessions.
- Results: record and review completed sessions.
- Ranking: win rate, comprehensive score, activity, and recent-form boards.
- Profile: personal stats, history, streaks, no-show count, and frequent partners.

## Core Flows

### Create And Join Session

1. Organizer creates a session with date, time, location, player count, and optional note.
2. The session appears on Home as the next table.
3. Players tap Join to reserve a seat.
4. Once confirmed players reach the configured count, the session state becomes Ready.
5. Additional players can join the waitlist.

### Cancel Or No-Show

1. A player may cancel before the session starts.
2. If cancellation leaves an empty seat, the first waitlisted player can be promoted.
3. Organizer can mark a confirmed player as no-show after the session.
4. No-shows reduce the player's comprehensive ranking score.

### Record Results

1. After a completed session, organizer opens Results and selects the session.
2. Organizer records either player ranks or win/loss points for the four players.
3. The submission enters Pending Confirmation.
4. Players can confirm the result.
5. After confirmation, the session becomes Completed and rankings refresh.

For version one, use rank-based entry as the default. Point-based entry can be included as a secondary mode if implementation cost is low.

## Ranking Rules

### Eligibility

Players need at least three completed sessions to enter official rankings. Players below the threshold appear in an Observation section so one lucky session cannot dominate the leaderboard.

### Win Rate

Win rate is calculated as:

`first_place_count / completed_session_count`

### Recent Form

Recent form reflects the last five completed sessions. Suggested labels:

- Hot: frequent top-two finishes or active winning streak.
- Stable: mostly middle results.
- Cold: repeated bottom finishes.
- Returning: recently active after a long gap.

### Activity

Activity is based on joined and completed sessions within the selected period. The app should favor completed attendance over signups.

### Comprehensive Score

The comprehensive ranking combines:

- Win rate contribution.
- Activity contribution.
- Recent form contribution.
- Winning streak bonus.
- No-show penalty.

The exact numeric weights can start as configurable constants. Recommended first version:

- Win rate: 45%.
- Activity: 25%.
- Recent form: 20%.
- Streak bonus: 10%.
- No-show penalty: subtract fixed points per no-show in the period.

## Data Model

### Player

- id
- displayName
- avatarUrl
- joinedAt
- completedSessionCount
- firstPlaceCount
- currentStreak
- noShowCount

### Session

- id
- title
- startsAt
- location
- seatCount
- note
- status: Open, Ready, InProgress, PendingResult, PendingConfirmation, Completed, Cancelled
- organizerId
- participantIds
- waitlistIds
- noShowPlayerIds

### Result

- id
- sessionId
- entries: playerId, rank, optional points
- submittedBy
- submittedAt
- confirmationPlayerIds
- status: PendingConfirmation, Confirmed, Disputed

### RankingSnapshot

- period: Week, Month, All
- playerId
- winRate
- completedSessionCount
- activityScore
- recentFormLabel
- comprehensiveScore
- rank
- eligibilityStatus

## Home Page Design

Home should answer three questions immediately:

- Can we play tonight?
- Who is already in?
- Who is currently leading the group?

The hero module shows the next session with time, location, seat count, confirmed player avatars, and a clear Join button. If the table is one player short, use a prominent "missing one seat" state.

Below the hero, show two highlight tiles: weekly leader and best partner or activity king. The ranking preview shows the top three comprehensive ranking players and links to the full leaderboard.

## Visual Direction

Use a retro mahjong-table feeling while keeping the app efficient:

- Main colors: mahjong green, warm ivory, vermilion red, and muted gold.
- Surfaces: flat, tactile blocks with crisp borders and small-radius cards.
- Typography: readable Chinese UI type with a slightly editorial heading style.
- Motion: small state transitions for joining, filling seats, and rank changes.

Avoid heavy casino styling. The mood should feel like a familiar friend-group scorecard, not gambling software.

## Error Handling

- Full session: show waitlist entry instead of Join.
- Duplicate join: keep the existing registration and show current status.
- Late cancellation: allow cancellation but flag it for organizer review.
- Conflicting result submissions: mark the result Disputed and keep rankings unchanged until resolved.
- Insufficient completed sessions: show the player in Observation instead of official rankings.

## Privacy And Trust

- Only group members can see sessions and rankings.
- Only organizers can submit results by default.
- Participants can confirm or dispute submitted results.
- Ranking changes are derived from confirmed results only.

## Version One Acceptance Criteria

- A user can create a session with time, location, seats, and note.
- Members can join, cancel, and waitlist for a session.
- Home clearly shows the next session status and ranking highlights.
- Organizer can submit rank-based results for a completed session.
- Confirmed results update player stats and rankings.
- Ranking tabs support week, month, and all-time periods.
- Players with fewer than three completed sessions are separated from official rankings.
- Profile shows personal win rate, completed sessions, streak, no-show count, and recent sessions.

## Out Of Scope

- Venue inventory or paid table reservations.
- WeChat Pay or any payment flow.
- Real-time chat.
- Hand-by-hand scoring.
- Tournament brackets.
- Public discovery of games outside the friend group.
