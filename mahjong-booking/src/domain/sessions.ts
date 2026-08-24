import type { Session } from "../types";

export function joinSession(session: Session, playerId: string): Session {
  if (!isBookableSession(session)) {
    return session;
  }

  if (
    session.participantIds.includes(playerId) ||
    session.waitlistIds.includes(playerId)
  ) {
    return session;
  }

  if (session.participantIds.length < session.seatCount) {
    const participantIds = [...session.participantIds, playerId];

    return {
      ...session,
      participantIds,
      status: participantIds.length >= session.seatCount ? "ready" : "open",
    };
  }

  return {
    ...session,
    waitlistIds: [...session.waitlistIds, playerId],
  };
}

export function cancelSeat(session: Session, playerId: string): Session {
  if (!isBookableSession(session)) {
    return session;
  }

  if (session.waitlistIds.includes(playerId)) {
    return {
      ...session,
      waitlistIds: session.waitlistIds.filter((id) => id !== playerId),
    };
  }

  if (!session.participantIds.includes(playerId)) {
    return session;
  }

  const participantIds = session.participantIds.filter((id) => id !== playerId);
  const [promotedPlayerId, ...waitlistIds] = session.waitlistIds;
  const nextParticipantIds = promotedPlayerId
    ? [...participantIds, promotedPlayerId]
    : participantIds;

  return {
    ...session,
    participantIds: nextParticipantIds,
    waitlistIds,
    status: nextParticipantIds.length >= session.seatCount ? "ready" : "open",
  };
}

function isBookableSession(session: Session): boolean {
  return session.status === "open" || session.status === "ready";
}
