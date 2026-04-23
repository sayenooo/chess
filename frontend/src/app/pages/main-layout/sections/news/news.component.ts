import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

interface NewsItem {
  title: string;
  date: string;
  summary: string;
  tag: string;
}

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './news.component.html',
  styleUrl: './news.component.css'
})
export class NewsComponent {
  readonly news: NewsItem[] = [
    { title: 'World Chess Championship 2026', date: 'Apr 20, 2026', summary: 'The World Chess Championship finals are set to begin next month with Ding Liren defending his title against a new challenger.', tag: 'Tournament' },
    { title: 'KBTU Chess Club Tournament Results', date: 'Apr 15, 2026', summary: 'Congratulations to all participants! Check out the final standings and notable games from our spring tournament.', tag: 'KBTU' },
    { title: 'New Opening Theory Discovered', date: 'Apr 10, 2026', summary: 'A novel approach to the Sicilian Defense has been gaining traction at the grandmaster level, reshaping opening preparation.', tag: 'Theory' },
    { title: 'Chess AI Reaches New Milestone', date: 'Apr 5, 2026', summary: 'Latest chess engines demonstrate unprecedented positional understanding, challenging our understanding of strategic play.', tag: 'Technology' },
    { title: 'Tips for Improving Your Endgame', date: 'Mar 28, 2026', summary: 'Five essential endgame techniques every intermediate player should master to climb the rating ladder.', tag: 'Education' },
  ];
}
