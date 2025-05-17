import { OAuth2Client } from 'google-auth-library';
import { calendar_v3, gmail_v1, google } from 'googleapis';
import * as fs from 'fs';
import * as readline from 'readline';

// Scopes define what APIs you're accessing
const SCOPES = [
  'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/gmail.readonly',
];

// Path to token and credentials
const CREDENTIALS_PATH = 'credentials.json';
const TOKEN_PATH = 'token.json';

interface Credentials {
  installed: {
    client_secret: string;
    client_id: string;
    redirect_uris: string[];
  };
}

// Load or request authorization
function authorize(callback: (auth: OAuth2Client) => void): void {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8')) as Credentials;
  const { client_secret, client_id, redirect_uris } = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  if (fs.existsSync(TOKEN_PATH)) {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
    oAuth2Client.setCredentials(token);
    callback(oAuth2Client);
  } else {
    getAccessToken(oAuth2Client, callback);
  }
}

function getAccessToken(oAuth2Client: OAuth2Client, callback: (auth: OAuth2Client) => void): void {
  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
  });

  console.log('🔗 Authorize this app by visiting this URL:\n', authUrl);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  rl.question('📥 Enter the code from that page here: ', (code) => {
    rl.close();
    oAuth2Client.getToken(code, (err, token) => {
      if (err) {
        console.error('❌ Error retrieving access token', err);
        return;
      }
      if (!token) {
        console.error('❌ No token received');
        return;
      }
      oAuth2Client.setCredentials(token);
      fs.writeFileSync(TOKEN_PATH, JSON.stringify(token));
      console.log('✅ Token saved to', TOKEN_PATH);
      callback(oAuth2Client);
    });
  });
}

// Fetch and print upcoming calendar events
function fetchCalendarEvents(auth: OAuth2Client): void {
  const calendar = google.calendar({ version: 'v3', auth }) as calendar_v3.Calendar;
  calendar.events.list(
    {
      calendarId: 'primary',
      timeMin: new Date().toISOString(),
      maxResults: 5,
      singleEvents: true,
      orderBy: 'startTime',
    },
    (err, res) => {
      if (err) {
        console.error('❌ Calendar API Error:', err);
        return;
      }
      const events = res?.data.items || [];
      console.log('\n📅 Upcoming Calendar Events:');
      if (events.length === 0) {
        console.log('No upcoming events found.');
      } else {
        events.forEach((event) => {
          const start = event.start?.dateTime || event.start?.date;
          console.log(`- ${event.summary} at ${start}`);
        });
      }
    }
  );
}

// Fetch and print recent email subjects
async function fetchGmailEmails(auth: OAuth2Client): Promise<void> {
  const gmail = google.gmail({ version: 'v1', auth }) as gmail_v1.Gmail;

  try {
    const res = await gmail.users.messages.list({ userId: 'me', maxResults: 5 });
    const messages = res.data.messages || [];

    console.log('\n📧 Recent Emails:');
    if (messages.length === 0) {
      console.log('No recent emails found.');
      return;
    }

    for (const msg of messages) {
      if (!msg.id) continue;
      const message = await gmail.users.messages.get({ userId: 'me', id: msg.id });
      const headers = message.data.payload?.headers || [];
      const subject = headers.find((h) => h.name === 'Subject')?.value;
      const from = headers.find((h) => h.name === 'From')?.value;
      console.log(`- Subject: ${subject}\n  From: ${from}\n`);
    }
  } catch (err) {
    console.error('❌ Gmail API Error:', err);
  }
}

// Main Execution
authorize((auth) => {
  fetchCalendarEvents(auth);
  fetchGmailEmails(auth);
});

