import { useEffect, useState } from 'react';

/* Temporary frontend team color map */
const TEAM_COLORS = {
  ARI: '#97233F',
  ATL: '#A71930',
  BAL: '#241773',
  BUF: '#00338D',
  CAR: '#0085CA',
  CHI: '#0B162A',
  CIN: '#FB4F14',
  CLE: '#311D00',
  DAL: '#041E42',
  DEN: '#FB4F14',
  DET: '#0076B6',
  GB:  '#203731',
  HOU: '#03202F',
  IND: '#002C5F',
  JAX: '#006778',
  KC:  '#E31837',
  LAC: '#0080C6',
  LAR: '#003594',
  LV:  '#000000',
  MIA: '#008E97',
  MIN: '#4F2683',
  NE:  '#002244',
  NO:  '#D3BC8D',
  NYG: '#0B2265',
  NYJ: '#125740',
  PHI: '#004C54',
  PIT: '#FFB612',
  SF:  '#AA0000',
  SEA: '#002244',
  TB:  '#D50A0A',
  TEN: '#4B92DB',
  WAS: '#5A1414'
};

const TeamHelmet = ({ teamId, size = 26 }) => {
  const [team, setTeam] = useState(null);

  useEffect(() => {
    if (!teamId) return;

    const fetchTeam = async () => {
      try {
        const apiUrl =
          import.meta.env.VITE_API_URL ||
          'https://smartline-production.up.railway.app';

        const res = await fetch(`${apiUrl}/teams/${teamId}`);
        if (!res.ok) return;

        const data = await res.json();
        setTeam(data);
      } catch (err) {
        console.error('Failed to fetch team for badge:', err);
      }
    };

    fetchTeam();
  }, [teamId]);

  if (!team) return null;

  const bgColor = TEAM_COLORS[team.abbrev] || '#64748b';

  return (
    <div
      className="flex items-center justify-center rounded-full flex-shrink-0"
      style={{
        width: size * 1.6,
        height: size * 1.6,
        backgroundColor: '#FFFFFF'
      }}
    >
        <div
        className="flex items-center justify-center rounded-full flex-shrink-0"
        style={{
            width: size * 1.5,
            height: size * 1.5,
            backgroundColor: bgColor
        }}
        >
        <img
            src={team.logo_url}
            alt={team.name}
            style={{
            width: size * 1.2,
            height: size * 1.2,
            objectFit: 'contain'
            }}
        />
        </div>
    </div>
  );
};

export default TeamHelmet;

