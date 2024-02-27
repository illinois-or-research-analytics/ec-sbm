/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                               *
 *	This program is free software; you can redistribute it and/or modify         *
 *  it under the terms of the GNU General Public License as published by         *
 *  the Free Software Foundation; either version 2 of the License, or            *
 *  (at your option) any later version.                                          *
 *                                                                               *
 *  This program is distributed in the hope that it will be useful,              *
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of               *
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                *
 *  GNU General Public License for more details.                                 *
 *                                                                               *
 *  You should have received a copy of the GNU General Public License            *
 *  along with this program; if not, write to the Free Software                  *
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA    *
 *                                                                               *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                               *
 *  Created by Andrea Lancichinetti on 7/01/09 (email: arg.lanci@gmail.com)      *
 *	Modified on 28/05/09                                                         *
 *	Collaborators: Santo Fortunato												 *
 *  Location: ISI foundation, Turin, Italy                                       *
 *	Project: Benchmarking community detection programs                           *
 *                                                                               *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

#include "./standard_include.cpp"
#define unlikely -214741

#include "set_parameters.cpp"

bool they_are_mate(int a, int b, const deque<deque<int>> &member_list)
{

	for (int i = 0; i < member_list[a].size(); i++)
	{

		if (binary_search(member_list[b].begin(), member_list[b].end(), member_list[a][i]))
			return true;
	}

	return false;
}

#include "cc.cpp"

// it computes the sum of a deque<int>

int deque_int_sum(const deque<int> &a)
{

	int s = 0;
	for (int i = 0; i < a.size(); i++)
		s += a[i];

	return s;
}

// it computes the integral of a power law
double integral(double a, double b)
{

	if (fabs(a + 1.) > 1e-10)
		return (1. / (a + 1.) * pow(b, a + 1.));

	else
		return (log(b));
}

// it returns the average degree of a power law
double average_degree(const double &dmax, const double &dmin, const double &gamma)
{

	return (1. / (integral(gamma, dmax) - integral(gamma, dmin))) * (integral(gamma + 1, dmax) - integral(gamma + 1, dmin));
}

// bisection method to find the inferior limit, in order to have the expected average degree
double solve_dmin(const double &dmax, const double &dmed, const double &gamma)
{

	double dmin_l = 1;
	double dmin_r = dmax;
	double average_k1 = average_degree(dmin_r, dmin_l, gamma);
	double average_k2 = dmin_r;

	if ((average_k1 - dmed > 0) || (average_k2 - dmed < 0))
	{

		cerr << "\n***********************\nERROR: the average degree is out of range:";

		if (average_k1 - dmed > 0)
		{
			cerr << "\nyou should increase the average degree (bigger than " << average_k1 << ")" << endl;
			cerr << "(or decrease the maximum degree...)" << endl;
		}

		if (average_k2 - dmed < 0)
		{
			cerr << "\nyou should decrease the average degree (smaller than " << average_k2 << ")" << endl;
			cerr << "(or increase the maximum degree...)" << endl;
		}

		return -1;
	}

	while (fabs(average_k1 - dmed) > 1e-7)
	{

		double temp = average_degree(dmax, ((dmin_r + dmin_l) / 2.), gamma);
		if ((temp - dmed) * (average_k2 - dmed) > 0)
		{

			average_k2 = temp;
			dmin_r = ((dmin_r + dmin_l) / 2.);
		}
		else
		{

			average_k1 = temp;
			dmin_l = ((dmin_r + dmin_l) / 2.);
		}
	}

	return dmin_l;
}

// it computes the correct (i.e. discrete) average of a power law
double integer_average(int n, int min, double tau)
{

	double a = 0;

	for (double h = min; h < n + 1; h++)
		a += pow((1. / h), tau);

	double pf = 0;
	for (double i = min; i < n + 1; i++)
		pf += 1 / a * pow((1. / (i)), tau) * i;

	return pf;
}

// this function changes the community sizes merging the smallest communities
int change_community_size(deque<int> &seq)
{

	if (seq.size() <= 2)
		return -1;

	int min1 = 0;
	int min2 = 0;

	for (int i = 0; i < seq.size(); i++)
		if (seq[i] <= seq[min1])
			min1 = i;

	if (min1 == 0)
		min2 = 1;

	for (int i = 0; i < seq.size(); i++)
		if (seq[i] <= seq[min2] && seq[i] > seq[min1])
			min2 = i;

	seq[min1] += seq[min2];

	int c = seq[0];
	seq[0] = seq[min2];
	seq[min2] = c;
	seq.pop_front();

	return 0;
}

int build_bipartite_network(deque<deque<int>> &member_matrix, const deque<int> &member_numbers, const deque<int> &num_seq)
{
	// E_in for each node
	deque<set<int>> en_in;
	{
		set<int> first;
		for (int i = 0; i < member_numbers.size(); i++)
		{
			en_in.push_back(first);
		}
	}

	// E_out for each community
	deque<set<int>> en_out;
	{
		set<int> first;
		for (int i = 0; i < num_seq.size(); i++)
		{
			en_out.push_back(first);
		}
	}

	multimap<int, int> degree_node_out;
	for (int i = 0; i < num_seq.size(); i++)
		degree_node_out.insert(make_pair(num_seq[i], i));

	cout << "degree_node_out" << endl;
	for (multimap<int, int>::iterator it = degree_node_out.begin(); it != degree_node_out.end(); it++)
		cout << it->first << " " << it->second << endl;
	cout << endl;

	deque<pair<int, int>> degree_node_in;
	for (int i = 0; i < member_numbers.size(); i++)
		degree_node_in.push_back(make_pair(member_numbers[i], i));

	cout << "degree_node_in" << endl;
	for (int i = 0; i < degree_node_in.size(); i++)
		cout << degree_node_in[i].first << " " << degree_node_in[i].second << endl;
	cout << endl;

	sort(degree_node_in.begin(), degree_node_in.end());

	// Greedily assign nodes to communities:
	// Consider nodes in descending order of degree, 
	// assign each node to the community with the current largest number of available slots

	cout << "Greedy assignment of nodes to communities" << endl;

	cout << "-- Start of the process --" << endl;
	deque<pair<int, int>>::iterator itlast = degree_node_in.end();
	while (itlast != degree_node_in.begin())
	{
		itlast--;

		multimap<int, int>::iterator itit = degree_node_out.end(); // largest community
		deque<multimap<int, int>::iterator> erasenda;

		cout << "-- Node " << itlast->second << " belonging to " << itlast->first << " communities" << endl;

		for (int i = 0; i < itlast->first; i++)
		{
			if (itit != degree_node_out.begin())
			{
				itit--;

				// cout << "Community " << itit->second << " with size " << itit->first << endl;

				en_in[itlast->second].insert(itit->second);
				en_out[itit->second].insert(itlast->second);

				erasenda.push_back(itit);
			}
			else
				return -1;
		}

		// cout << "en_in" << endl;
		// for (int i = 0; i < en_in.size(); i++)
		// {
		// 	cout << i << ": ";
		// 	for (set<int>::iterator its = en_in[i].begin(); its != en_in[i].end(); its++)
		// 		cout << *its << " ";
		// 	cout << endl;
		// }

		cout << "Community list after assigning node " << itlast->second << " to " << itit->second << endl;
		for (int i = 0; i < en_out.size(); i++)
		{
			cout << i << ": ";
			for (set<int>::iterator its = en_out[i].begin(); its != en_out[i].end(); its++)
				cout << *its << " ";
			cout << endl;
		}

		for (int i = 0; i < erasenda.size(); i++)
		{
			if (erasenda[i]->first > 1)
				degree_node_out.insert(make_pair(erasenda[i]->first - 1, erasenda[i]->second));

			degree_node_out.erase(erasenda[i]);
		}
	}
	cout << "-- End of the process --" << endl;

	cout << "en_in" << endl;
	for (int i = 0; i < en_in.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en_in[i].begin(); its != en_in[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "en_out" << endl;
	for (int i = 0; i < en_out.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en_out[i].begin(); its != en_out[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "----------------------------------------------------------" << endl;

	deque<int> degree_list;
	for (int kk = 0; kk < member_numbers.size(); kk++)
		for (int k2 = 0; k2 < member_numbers[kk]; k2++)
			degree_list.push_back(kk);

	cout << "Node list (duplicate nodes belonging to multiple communities)" << endl;
	for (int i = 0; i < degree_list.size(); i++)
		cout << degree_list[i] << " ";
	cout << endl;

	// For 10 rounds,
	// For each community, do community_size iterations,
	// Randomly choose a node
	// If the node is in the community, do nothing
	// If the node is not in the community, randomly choose a node in the community and switch them

	cout << "Randomly change community assignment" << endl;

	cout << "-- Start of the process --" << endl;
	for (int run = 0; run < 10; run++) {
		cout << "-- Run " << run << endl;
		for (int node_a = 0; node_a < num_seq.size(); node_a++) {
			cout << "---- Community " << node_a << "/" << num_seq.size() << endl;

			for (int krm = 0; krm < en_out[node_a].size(); krm++)
			{
				cout << "------ Iter " << krm << "/" << en_out[node_a].size() << endl;

				int random_mate = degree_list[irand(degree_list.size() - 1)];

				cout << "Random node " << random_mate << " ";

				if (en_out[node_a].find(random_mate) == en_out[node_a].end())
				{
					cout << "NOT in the community. Proceed." << endl;

					deque<int> external_nodes;
					for (set<int>::iterator it_est = en_out[node_a].begin(); it_est != en_out[node_a].end(); it_est++)
						external_nodes.push_back(*it_est);

					cout << "Nodes in the community: ";
					for (int i = 0; i < external_nodes.size(); i++)
						cout << external_nodes[i] << " ";
					cout << "| ";

					int old_node = external_nodes[irand(external_nodes.size() - 1)];

					cout << "Choose old node inside community: " << old_node << endl;

					deque<int> not_common;
					for (set<int>::iterator it_est = en_in[random_mate].begin(); it_est != en_in[random_mate].end(); it_est++)
						if (en_in[old_node].find(*it_est) == en_in[old_node].end())
							not_common.push_back(*it_est);

					cout << "Communities of random node that do not share with the old node: ";
					for (int i = 0; i < not_common.size(); i++)
						cout << not_common[i] << " ";
					cout << endl;

					if (not_common.empty()) {
						cout << "Two nodes share the same communities. Do nothing." << endl;
						break;
					}

					int node_h = not_common[irand(not_common.size() - 1)];

					en_out[node_a].insert(random_mate);
					en_out[node_a].erase(old_node);

					en_in[old_node].insert(node_h);
					en_in[old_node].erase(node_a);

					en_in[random_mate].insert(node_a);
					en_in[random_mate].erase(node_h);

					en_out[node_h].erase(random_mate);
					en_out[node_h].insert(old_node);

					cout << "Switch node " << random_mate << " from community " << node_h << " to community " << node_a << endl;
					cout << "Switch node " << old_node << " from community " << node_a << " to community " << node_h << endl;

					cout << "Communities after switching: " << endl;
					for (int i = 0; i < en_out.size(); i++)
					{
						cout << i << ": ";
						for (set<int>::iterator its = en_out[i].begin(); its != en_out[i].end(); its++)
							cout << *its << " ";
						cout << endl;
					}
				}
				else {
					cout << "in the community. Do nothing." << endl;
				}

				cout << "------" << endl;
			}
			cout << "----" << endl;
		}
		cout << "--" << endl;
	}

	member_matrix.clear();
	deque<int> first;

	for (int i = 0; i < en_out.size(); i++)
	{
		member_matrix.push_back(first);
		for (set<int>::iterator its = en_out[i].begin(); its != en_out[i].end(); its++)
			member_matrix[i].push_back(*its);
	}

	return 0;
}

int internal_degree_and_membership(
	double mixing_parameter,
	int overlapping_nodes, int max_mem_num,
	int num_nodes,
	deque<deque<int>> &member_matrix,
	bool excess, bool defect,
	deque<int> &degree_seq,
	deque<int> &num_seq,
	deque<int> &internal_degree_seq,
	bool fixed_range, int nmin, int nmax, double tau2)
{
	cout << "Internal degree and membership" << endl;

	if (num_nodes < overlapping_nodes)
	{
		cerr << "\n***********************\nERROR: there are more overlapping nodes than nodes in the whole network! Please, decrease the former ones or increase the latter ones" << endl;
		return -1;
	}

	member_matrix.clear();
	internal_degree_seq.clear();

	cout << "Assigning the internal degree to each node..." << endl;

	int max_degree_actual = 0;
	for (int i = 0; i < degree_seq.size(); i++)
	{
		cout << "---- Node " << i << endl;

		double interno = (1 - mixing_parameter) * degree_seq[i];
		int int_interno = int(interno);
		cout << "Degree " << degree_seq[i] << " and internal degree " << interno << " (float) and " << int_interno << " (int)" << endl;
		if (ran4() < (interno - int_interno))
		{
			cout << "Added 1 to internal degree with probability " << (interno - int_interno) << endl;
			int_interno++;
		}
		cout << "Internal degree (final): " << int_interno << endl;

		if (excess)
		{
			while ((double(int_interno) / degree_seq[i] < (1 - mixing_parameter)) && (int_interno < degree_seq[i]))
				int_interno++;
		}

		if (defect)
		{
			while ((double(int_interno) / degree_seq[i] > (1 - mixing_parameter)) && (int_interno > 0))
				int_interno--;
		}

		internal_degree_seq.push_back(int_interno);

		if (int_interno > max_degree_actual)
			max_degree_actual = int_interno;
	}

	cout << "---" << endl;
	cout << "Max degree actual: " << max_degree_actual << endl;

	cout << "----------------------------------------------------------" << endl;

	deque<double> cumulative;
	powerlaw(nmax, nmin, tau2, cumulative);

	cout << "Cumulative distribution for the community sizes:" << endl;
	for (int i = 0; i < cumulative.size(); i++)
		cout << cumulative[i] << " ";
	cout << endl;

	if (num_seq.empty())
	{
		cout << "Community sizes are not provided" << endl;

		int _num_ = 0;

		if (!fixed_range && (max_degree_actual + 1) > nmin)
		{
			cout << "Fixed range: false" << endl;
			cout << "Max degree + 1 > min community size" << endl;

			_num_ = max_degree_actual + 1; // this helps the assignment of the memberships (it assures that at least one module is big enough to host each node)
			num_seq.push_back(max_degree_actual + 1);
		}

		while (true)
		{
			int nn = lower_bound(cumulative.begin(), cumulative.end(), ran4()) - cumulative.begin() + nmin;

			if (nn + _num_ <= num_nodes + overlapping_nodes * (max_mem_num - 1))
			{
				num_seq.push_back(nn);
				_num_ += nn;
			}
			else
				break;
		}

		num_seq[min_element(num_seq.begin(), num_seq.end()) - num_seq.begin()] += num_nodes + overlapping_nodes * (max_mem_num - 1) - _num_;
	}

	cout << "Number of communities: " << num_seq.size() << endl;
	cout << "Community sizes sequence:" << endl;
	for (int i = 0; i < num_seq.size(); i++)
		cout << num_seq[i] << " ";
	cout << endl;

	cout << "----------------------------------------------------------" << endl;

	deque<int> member_numbers;
	for (int i = 0; i < overlapping_nodes; i++)
		member_numbers.push_back(max_mem_num);
	for (int i = overlapping_nodes; i < degree_seq.size(); i++)
		member_numbers.push_back(1);

	cout << "Number of community each node belongs to:" << endl;
	for (int i = 0; i < member_numbers.size(); i++)
		cout << member_numbers[i] << " ";
	cout << endl;

	cout << "----------------------------------------------------------" << endl;

	if (build_bipartite_network(member_matrix, member_numbers, num_seq) == -1)
	{
		cerr << "it seems that the overlapping nodes need more communities that those I provided. Please increase the number of communities or decrease the number of overlapping nodes" << endl;
		return -1;
	}

	cout << "Community memberships:" << endl;
	for (int i = 0; i < member_matrix.size(); i++)
	{
		cout << i << ": ";
		for (int j = 0; j < member_matrix[i].size(); j++)
			cout << member_matrix[i][j] << " (" << degree_seq[member_matrix[i][j]] << ") ";
		cout << endl;
	}

	cout << "Number of community each node belongs to:" << endl;
	for (int i = 0; i < member_numbers.size(); i++)
		cout << member_numbers[i] << " ";
	cout << endl;

	cout << "Community sizes:" << endl;
	for (int i = 0; i < num_seq.size(); i++)
		cout << num_seq[i] << " ";
	cout << endl;

	cout << "----------------------------------------------------------" << endl;

	deque<int> available;
	for (int i = 0; i < num_nodes; i++)
		available.push_back(0);

	for (int i = 0; i < member_matrix.size(); i++)
	{
		for (int j = 0; j < member_matrix[i].size(); j++)
			available[member_matrix[i][j]] += member_matrix[i].size() - 1;
	}

	cout << "Availability (# other nodes in the same community)" << endl;
	for (int i = 0; i < available.size(); i++)
		cout << available[i] << " ";
	cout << endl;

	deque<int> available_nodes;
	for (int i = 0; i < num_nodes; i++)
		available_nodes.push_back(i);

	cout << "Available nodes (all the nodes): ";
	for (int i = 0; i < available_nodes.size(); i++)
		cout << available_nodes[i] << " ";
	cout << endl;

	cout << "-- Start of the process --" << endl;

	// Find a random permutation of the nodes such that
	// the availability of the node is consistent with
	// the internal degree of the node

	deque<int> map_nodes; // in the position i there is the new name of the node i
	for (int i = 0; i < num_nodes; i++)
		map_nodes.push_back(0);

	cout << "From higher to lower degree" << endl;
	for (int i = degree_seq.size() - 1; i >= 0; i--)
	{
		int &degree_here = internal_degree_seq[i];

		cout << "---- Node " << i << " with internal degree " << degree_here << endl;

		int try_this = irand(available_nodes.size() - 1);

		cout << "(try 0) Random node " << available_nodes[try_this] << " with internal degree " << degree_here << " vs availability " << available[available_nodes[try_this]] << endl;

		int kr = 0;
		while (internal_degree_seq[i] > available[available_nodes[try_this]])
		{
			kr++;
			try_this = irand(available_nodes.size() - 1);
			cout << "(try " << kr << ") Random node " << available_nodes[try_this] << " with availability " << available[available_nodes[try_this]] << endl;
			if (kr == 3 * num_nodes)
			{

				if (change_community_size(num_seq) == -1)
				{

					cerr << "\n***********************\nERROR: this program needs more than one community to work fine" << endl;
					return -1;
				}

				cout << "it took too long to decide the memberships; I will try to change the community sizes" << endl;

				cout << "new community sizes" << endl;
				for (int i = 0; i < num_seq.size(); i++)
					cout << num_seq[i] << " ";
				cout << endl
					 << endl;

				return (internal_degree_and_membership(mixing_parameter, overlapping_nodes, max_mem_num, num_nodes, member_matrix, excess, defect, degree_seq, num_seq, internal_degree_seq, fixed_range, nmin, nmax, tau2));
			}
		}

		cout << "Found node " << available_nodes[try_this] << " with enough availability" << endl;

		map_nodes[available_nodes[try_this]] = i;

		cout << "Map nodes " << available_nodes[try_this] << " to " << i << endl;

		available_nodes[try_this] = available_nodes[available_nodes.size() - 1];
		available_nodes.pop_back();

		cout << "Available nodes (after removing " << available_nodes[try_this] << "): ";
		for (int i = 0; i < available_nodes.size(); i++)
			cout << available_nodes[i] << " ";
		cout << endl;
	}

	cout << "-- End of the process --" << endl;

	cout << "Map nodes: ";
	for (int i = 0; i < map_nodes.size(); i++)
		cout << map_nodes[i] << " ";
	cout << endl;

	for (int i = 0; i < member_matrix.size(); i++)
	{
		for (int j = 0; j < member_matrix[i].size(); j++)
			member_matrix[i][j] = map_nodes[member_matrix[i][j]];
	}

	cout << "Member matrix" << endl;
	for (int i = 0; i < member_matrix.size(); i++)
	{
		cout << i << ": ";
		for (int j = 0; j < member_matrix[i].size(); j++)
			cout << member_matrix[i][j] << " (" << degree_seq[member_matrix[i][j]] << ") ";
		cout << endl;
	}

	for (int i = 0; i < member_matrix.size(); i++)
		sort(member_matrix[i].begin(), member_matrix[i].end());

	return 0;
}

int compute_internal_degree_per_node(int d, int m, deque<int> &a)
{
	// d is the internal degree
	// m is the number of memebership
	a.clear();
	int d_i = d / m;
	for (int i = 0; i < m; i++)
		a.push_back(d_i);

	for (int i = 0; i < d % m; i++)
		a[i]++;

	return 0;
}

int build_subgraph(
	deque<set<int>> &E, 
	const deque<int> &nodes, 
	const deque<int> &degrees)
{
	if (degrees.size() < 3)
	{
		cerr << "it seems that some communities should have only 2 nodes! This does not make much sense (in my opinion) Please change some parameters!" << endl;
		return -1;
	}

	// this function is to build a network with the labels stored in nodes and the degree seq in degrees (correspondence is based on the vectorial index)
	// the only complication is that you don't want the nodes to have neighbors they already have

	// labels will be placed in the end
	deque<set<int>> en; // this is the E of the subgraph
	{
		set<int> first;
		for (int i = 0; i < nodes.size(); i++)
			en.push_back(first);
	}

	multimap<int, int> degree_node;
	for (int i = 0; i < degrees.size(); i++)
		degree_node.insert(degree_node.end(), make_pair(degrees[i], i));

	cout << "Degree node" << endl;
	for (multimap<int, int>::iterator it = degree_node.begin(); it != degree_node.end(); it++)
		cout << it->first << " " << it->second << endl;
	cout << endl;

	int var = 0;

	while (degree_node.size() > 0)
	{
		multimap<int, int>::iterator itlast = degree_node.end();
		itlast--;

		cout << "-- Node " << itlast->second << " with degree " << itlast->first << endl;

		multimap<int, int>::iterator itit = itlast;
		deque<multimap<int, int>::iterator> erasenda;

		int inserted = 0;

		cout << "Connect with nodes: ";

		for (int i = 0; i < itlast->first; i++)
		{

			if (itit != degree_node.begin())
			{

				itit--;

				cout << itit->second << " ";

				en[itlast->second].insert(itit->second);
				en[itit->second].insert(itlast->second);
				inserted++;

				erasenda.push_back(itit);
			}

			else
				break;
		}

		cout << endl;

		for (int i = 0; i < erasenda.size(); i++)
		{

			if (erasenda[i]->first > 1)
				degree_node.insert(make_pair(erasenda[i]->first - 1, erasenda[i]->second));

			degree_node.erase(erasenda[i]);
		}

		var += itlast->first - inserted;
		degree_node.erase(itlast);
	}

	cout << endl;

	cout << "Edge list after greedy" << endl;
	for (int i = 0; i < en.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "---------" << endl;

	deque<int> degree_list;
	for (int kk = 0; kk < degrees.size(); kk++)
		for (int k2 = 0; k2 < degrees[kk]; k2++)
			degree_list.push_back(kk);

	cout << "Degree list (repeat the same node = their degree)" << endl;
	for (int i = 0; i < degree_list.size(); i++)
		cout << degree_list[i] << " ";
	cout << endl;

	// this is to randomize the subgraph -------------------------------------------------------------------

	for (int run = 0; run < 10; run++) {
		cout << "-- Run " << run + 1 << "/10 --" << endl;

		for (int node_a = 0; node_a < degrees.size(); node_a++) {
			cout << "---- Node i = " << node_a << " with degree " << degrees[node_a] << " ----" << endl;

			for (int krm = 0; krm < en[node_a].size(); krm++)
			{
				cout << "------ Iter " << krm + 1 << "/" << en[node_a].size() << " ------" << endl;

				int random_mate = degree_list[irand(degree_list.size() - 1)];
				while (random_mate == node_a)
					random_mate = degree_list[irand(degree_list.size() - 1)];

				cout << "Random another node j (proportionally to degree): " << random_mate << endl;

				if (en[node_a].insert(random_mate).second)
				{

					deque<int> out_nodes;
					for (set<int>::iterator it_est = en[node_a].begin(); it_est != en[node_a].end(); it_est++)
						if ((*it_est) != random_mate)
							out_nodes.push_back(*it_est);

					int old_node = out_nodes[irand(out_nodes.size() - 1)];

					en[node_a].erase(old_node);
					en[random_mate].insert(node_a);
					en[old_node].erase(node_a);

					deque<int> not_common;
					for (set<int>::iterator it_est = en[random_mate].begin(); it_est != en[random_mate].end(); it_est++)
						if ((old_node != (*it_est)) && (en[old_node].find(*it_est) == en[old_node].end()))
							not_common.push_back(*it_est);

					int node_h = not_common[irand(not_common.size() - 1)];

					en[random_mate].erase(node_h);
					en[node_h].erase(random_mate);
					en[node_h].insert(old_node);
					en[old_node].insert(node_h);

					cout << "Pick randomly a node k (neighbor of i not j): " << old_node << endl;
					cout << "Remove link between (k) " << old_node << " and (i) " << node_a << endl; 
					cout << "Pick randomly a node h (neighbor of j that is not k or neighbors of k): " << node_h << endl;


					cout << "Add link between (i) " << node_a << " and (j) " << random_mate << endl;
					cout << "Remove link between (k) " << old_node << " and (i) " << node_a << endl; 
					cout << "Add link between (h) " << node_h << " and (k) " << old_node << endl;
					cout << "Remove link between (h) " << node_h << " and (j) " << random_mate << endl;

					cout << "Edge list after rewiring" << endl;
					for (int i = 0; i < en.size(); i++)
					{
						cout << i << ": ";
						for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
							cout << *its << " ";
						cout << endl;
					}
					cout << endl;
				}
			}
		}
	}

	cout << "Local edge list after randomization" << endl;
	for (int i = 0; i < en.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "Adding new links from previous" << endl;

	deque<pair<int, int>> multiple_edge;
	for (int i = 0; i < en.size(); i++)
	{
		cout << "Node " << i << endl;

		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++) {
			cout << "Neighbor " << *its << endl;

			if (i < *its)
			{
				cout << "Since " << i << " < " << *its << ", I will add a link between them" << endl;

				bool already = !(E[nodes[i]].insert(nodes[*its]).second);
				if (already) {
					cout << "There is already a link between " << nodes[i] << " and " << nodes[*its] << endl;
					multiple_edge.push_back(make_pair(nodes[i], nodes[*its]));
				}
				else {
					cout << "There is no link between " << nodes[i] << " and " << nodes[*its] << endl;
					cout << "Add a link between " << nodes[i] << " and " << nodes[*its] << endl;
					E[nodes[*its]].insert(nodes[i]);
				}
			}
		}
	}

	cout << "Edge list after adding new links" << endl;
	for (int i = 0; i < E.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = E[i].begin(); its != E[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "---------" << endl;

	cout << "Multiple links" << endl;
	for (int i = 0; i < multiple_edge.size(); i++)
		cout << multiple_edge[i].first << " " << multiple_edge[i].second << endl;
	cout << endl;

	for (int i = 0; i < multiple_edge.size(); i++)
	{

		int &a = multiple_edge[i].first;
		int &b = multiple_edge[i].second;

		// now, I'll try to rewire this multiple link among the nodes stored in nodes.
		int stopper_ml = 0;

		while (true)
		{

			stopper_ml++;

			int random_mate = nodes[degree_list[irand(degree_list.size() - 1)]];
			while (random_mate == a || random_mate == b)
				random_mate = nodes[degree_list[irand(degree_list.size() - 1)]];

			if (E[a].find(random_mate) == E[a].end())
			{

				deque<int> not_common;
				for (set<int>::iterator it_est = E[random_mate].begin(); it_est != E[random_mate].end(); it_est++)
					if ((b != (*it_est)) && (E[b].find(*it_est) == E[b].end()) && (binary_search(nodes.begin(), nodes.end(), *it_est)))
						not_common.push_back(*it_est);

				if (not_common.size() > 0)
				{

					int node_h = not_common[irand(not_common.size() - 1)];

					E[random_mate].insert(a);
					E[random_mate].erase(node_h);

					E[node_h].erase(random_mate);
					E[node_h].insert(b);

					E[b].insert(node_h);
					E[a].insert(random_mate);

					break;
				}
			}

			if (stopper_ml == 2 * E.size())
			{

				cout << "sorry, I need to change the degree distribution a little bit (one less link)" << endl;
				break;
			}
		}
	}

	return 0;
}

int build_subgraphs(
	deque<set<int>> &E, 
	const deque<deque<int>> &member_matrix, 
	deque<deque<int>> &member_list,
	deque<deque<int>> &link_list, 
	const deque<int> &internal_degree_seq, 
	const deque<int> &degree_seq, 
	const bool excess, const bool defect)
{
	E.clear();
	member_list.clear();
	link_list.clear();

	int num_nodes = degree_seq.size();
	{
		deque<int> first;
		for (int i = 0; i < num_nodes; i++)
			member_list.push_back(first);
	}

	for (int i = 0; i < member_matrix.size(); i++)
		for (int j = 0; j < member_matrix[i].size(); j++)
			member_list[member_matrix[i][j]].push_back(i);

	cout << "Member list (not changing from member matrix)" << endl;
	for (int i = 0; i < member_list.size(); i++)
	{
		cout << i << ": ";
		for (int j = 0; j < member_list[i].size(); j++)
			cout << member_list[i][j] << " ";
		cout << endl;
	}
	cout << endl;

	for (int i = 0; i < member_list.size(); i++)
	{
		deque<int> liin;

		for (int j = 0; j < member_list[i].size(); j++)
		{
			compute_internal_degree_per_node(internal_degree_seq[i], member_list[i].size(), liin);
			liin.push_back(degree_seq[i] - internal_degree_seq[i]);
		}
		link_list.push_back(liin);
	}

	cout << "Internal + external degree of each node" << endl;
	for (int i = 0; i < link_list.size(); i++)
	{
		cout << i << ": ";
		for (int j = 0; j < link_list[i].size(); j++)
			cout << link_list[i][j] << " ";
		cout << endl;
	}
	cout << endl;

	// Check if internal degree of each community is even

	for (int i = 0; i < member_matrix.size(); i++)
	{
		int internal_cluster = 0;
		for (int j = 0; j < member_matrix[i].size(); j++)
		{
			int right_index = lower_bound(member_list[member_matrix[i][j]].begin(), member_list[member_matrix[i][j]].end(), i) - member_list[member_matrix[i][j]].begin();
			internal_cluster += link_list[member_matrix[i][j]][right_index];
		}
		cout << "Total internal degree of community " << i << " is " << internal_cluster << endl;

		if (internal_cluster % 2 != 0)
		{
			cout << "Internal degree of community " << i << " is not even" << endl;

			bool default_flag = false;
			if (excess)
				default_flag = true;
			else if (defect)
				default_flag = false;
			else if (ran4() > 0.5)
				default_flag = true;

			if (default_flag)
			{
				cout << "Default flag is true" << endl;

				// if this does not work in a reasonable time the degree sequence will be changed
				for (int j = 0; j < member_matrix[i].size(); j++)
				{

					int random_mate = member_matrix[i][irand(member_matrix[i].size() - 1)];

					int right_index = lower_bound(member_list[random_mate].begin(), member_list[random_mate].end(), i) - member_list[random_mate].begin();

					if ((link_list[random_mate][right_index] < member_matrix[i].size() - 1) && (link_list[random_mate][link_list[random_mate].size() - 1] > 0))
					{

						link_list[random_mate][right_index]++;
						link_list[random_mate][link_list[random_mate].size() - 1]--;

						break;
					}
				}
			}
			else
			{
				cout << "Default flag is false. Changing the degree" << endl;

				for (int j = 0; j < member_matrix[i].size(); j++)
				{
					int random_mate = member_matrix[i][irand(member_matrix[i].size() - 1)];

					cout << "(try " << j << ") Random mate " << random_mate << " with external degree " << link_list[random_mate][link_list[random_mate].size() - 1] << endl;

					int right_index = lower_bound(member_list[random_mate].begin(), member_list[random_mate].end(), i) - member_list[random_mate].begin();

					if (link_list[random_mate][right_index] > 0)
					{
						cout << "Internal degree of node " << random_mate << " is " << link_list[random_mate][right_index] << " which is positive." << endl;
						cout << "Reduce internal degree of node " << random_mate << " and increase external degree by 1." << endl;
						link_list[random_mate][right_index]--;
						link_list[random_mate][link_list[random_mate].size() - 1]++;
						break;
					}
				}

				cout << "Internal + external degree after changing the degree" << endl;
				for (int i = 0; i < link_list.size(); i++)
				{
					cout << i << ": ";
					for (int j = 0; j < link_list[i].size(); j++)
						cout << link_list[i][j] << " ";
					cout << endl;
				}
				cout << endl;
			}
		}
	}

	cout << "----------------------------------------------------------" << endl;

	{
		set<int> first;
		for (int i = 0; i < num_nodes; i++)
			E.push_back(first);
	}

	for (int i = 0; i < member_matrix.size(); i++)
	{
		deque<int> internal_degree_i;
		for (int j = 0; j < member_matrix[i].size(); j++)
		{
			int right_index = lower_bound(member_list[member_matrix[i][j]].begin(), member_list[member_matrix[i][j]].end(), i) - member_list[member_matrix[i][j]].begin();

			internal_degree_i.push_back(link_list[member_matrix[i][j]][right_index]);
		}

		cout << "-- Building subgraph for community " << i << " with nodes ";
		for (int j = 0; j < internal_degree_i.size(); j++)
			cout << member_matrix[i][j] << " (" << internal_degree_i[j] << ") ";
		cout << endl;

		if (build_subgraph(E, member_matrix[i], internal_degree_i) == -1)
			return -1;

		cout << "Edge list" << endl;
		for (int i = 0; i < E.size(); i++)
		{
			cout << i << ": ";
			for (set<int>::iterator its = E[i].begin(); its != E[i].end(); its++)
				cout << *its << " ";
			cout << endl;
		}
		cout << endl;
	}

	return 0;
}

int connect_all_the_parts(
	deque<set<int>> &E, 
	const deque<deque<int>> &member_list, 
	const deque<deque<int>> &link_list)
{
	deque<int> degrees;
	for (int i = 0; i < link_list.size(); i++)
		degrees.push_back(link_list[i][link_list[i].size() - 1]);

	cout << "External degree sequence" << endl;
	for (int i = 0; i < degrees.size(); i++)
		cout << degrees[i] << " ";
	cout << endl;

	deque<set<int>> en; // this is the en of the subgraph
	{
		set<int> first;
		for (int i = 0; i < member_list.size(); i++)
			en.push_back(first);
	}

	multimap<int, int> degree_node;
	for (int i = 0; i < degrees.size(); i++)
		degree_node.insert(degree_node.end(), make_pair(degrees[i], i));

	cout << "Degree node" << endl;
	for (multimap<int, int>::iterator it = degree_node.begin(); it != degree_node.end(); it++)
		cout << it->first << " " << it->second << endl;
	cout << endl;

	int var = 0;

	// For node in descending order of (external) degree
	// Connect with other nodes in descending order of (external) degree

	cout << "3.3.1. Add edges greedily" << endl;

	while (degree_node.size() > 0)
	{
		multimap<int, int>::iterator itlast = degree_node.end();
		itlast--;

		cout << "-- Node " << itlast->second << " with degree " << itlast->first << endl;

		multimap<int, int>::iterator itit = itlast;
		deque<multimap<int, int>::iterator> erasenda;

		int inserted = 0;

		cout << "Connect with nodes: ";

		for (int i = 0; i < itlast->first; i++)
		{

			if (itit != degree_node.begin())
			{
				itit--;
				
				cout << itit->second << " ";

				en[itlast->second].insert(itit->second);
				en[itit->second].insert(itlast->second);
				inserted++;

				erasenda.push_back(itit);
			}
			else
				break;
		}

		cout << endl;

		for (int i = 0; i < erasenda.size(); i++)
		{

			if (erasenda[i]->first > 1)
				degree_node.insert(make_pair(erasenda[i]->first - 1, erasenda[i]->second));

			degree_node.erase(erasenda[i]);
		}

		var += itlast->first - inserted;
		degree_node.erase(itlast);
	}
	cout << endl;

	cout << "Background graph edge list" << endl;
	for (int i = 0; i < en.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}
	cout << endl;

	cout << "----------------------------------------------------------" << endl;

	cout << "4.3.2. Randomize the background graph" << endl;

	deque<int> degree_list;
	for (int kk = 0; kk < degrees.size(); kk++)
		for (int k2 = 0; k2 < degrees[kk]; k2++)
			degree_list.push_back(kk);

	cout << "Degree list (repeat the same node = their degree)" << endl;
	for (int i = 0; i < degree_list.size(); i++)
		cout << degree_list[i] << " ";
	cout << endl;

	for (int run = 0; run < 10; run++) {
		cout << "-- Run " << run + 1 << "/10 --" << endl;

		for (int node_a = 0; node_a < degrees.size(); node_a++) {
			cout << "---- Node i = " << node_a << " with degree " << degrees[node_a] << " ----" << endl;

			for (int krm = 0; krm < en[node_a].size(); krm++)
			{
				cout << "------ Iter " << krm + 1 << "/" << en[node_a].size() << " ------" << endl;

				int random_mate = degree_list[irand(degree_list.size() - 1)];
				while (random_mate == node_a)
					random_mate = degree_list[irand(degree_list.size() - 1)];

				cout << "Random another node j (proportionally to degree): " << random_mate << endl;

				// cout << "Before insertion: ";
				// for (set<int>::iterator its = en[node_a].begin(); its != en[node_a].end(); its++)
				// 	cout << *its << " ";
				// cout << endl;

				if (en[node_a].insert(random_mate).second)
				{
					// cout << "After insertion: ";
					// for (set<int>::iterator its = en[node_a].begin(); its != en[node_a].end(); its++)
					// 	cout << *its << " ";
					// cout << endl;
					en[random_mate].insert(node_a);
					cout << "Add link between (i) " << node_a << " and (j) " << random_mate << endl;

					deque<int> out_nodes;
					for (set<int>::iterator it_est = en[node_a].begin(); it_est != en[node_a].end(); it_est++)
						if ((*it_est) != random_mate)
							out_nodes.push_back(*it_est);

					// cout << "Out nodes (neighbor of i but not j): ";
					// for (int i = 0; i < out_nodes.size(); i++)
					// 	cout << out_nodes[i] << " ";
					// cout << endl;

					int old_node = out_nodes[irand(out_nodes.size() - 1)];

					cout << "Pick randomly a node k (neighbor of i not j): " << old_node << endl;

					en[node_a].erase(old_node);
					en[old_node].erase(node_a);

					cout << "Remove link between (k) " << old_node << " and (i) " << node_a << endl; 
					// cout << "Add link from " << random_mate << " to " << node_a << endl;

					deque<int> not_common;
					for (set<int>::iterator it_est = en[random_mate].begin(); it_est != en[random_mate].end(); it_est++)
						if ((old_node != (*it_est)) && (en[old_node].find(*it_est) == en[old_node].end()))
							not_common.push_back(*it_est);

					// cout << "Not common nodes (neighbor of j that is not k or neighbors of k): ";
					// for (int i = 0; i < not_common.size(); i++)
					// 	cout << not_common[i] << " ";
					// cout << endl;

					int node_h = not_common[irand(not_common.size() - 1)];

					cout << "Pick randomly a node h (neighbor of j that is not k or neighbors of k): " << node_h << endl;

					en[random_mate].erase(node_h);
					en[node_h].erase(random_mate);
					en[node_h].insert(old_node);
					en[old_node].insert(node_h);

					cout << "Remove link between (h) " << node_h << " and (j) " << random_mate << endl;
					cout << "Add link between (h) " << node_h << " and (k) " << old_node << endl;

					cout << "Edge list after rewiring" << endl;
					for (int i = 0; i < en.size(); i++)
					{
						cout << i << ": ";
						for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
							cout << *its << " ";
						cout << endl;
					}
					cout << endl;
				}
			}
		}
	}

	cout << "---- End of process ----" << endl;

	cout << "Edge list after randomization" << endl;
	for (int i = 0; i < en.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}
	cout << endl;

	cout << "----------------------------------------------------------" << endl;

	cout << "4.3.3. Remove internal links" << endl;

	int var_mate = 0;
	for (int i = 0; i < degrees.size(); i++)
		for (set<int>::iterator itss = en[i].begin(); itss != en[i].end(); itss++)
			if (they_are_mate(i, *itss, member_list))
			{
				var_mate++;
			}
	
	cout << "Number of mate nodes (same community): " << var_mate << endl;

	// cout<<"var mate = "<<var_mate<<endl;

	int stopper_mate = 0;
	int mate_trooper = 10;

	while (var_mate > 0)
	{
		cout << "-- Current number of mate nodes (same community): " << var_mate << endl;

		int best_var_mate = var_mate;

		// ************************************************  rewiring

		for (int a = 0; a < degrees.size(); a++) {
			cout << "---- Node i = " << a << " ----" << endl;

			for (set<int>::iterator its = en[a].begin(); its != en[a].end(); its++) {
				cout << "------ Neighbor j = " << *its << " ------" << endl;

				if (they_are_mate(a, *its, member_list))
				{
					cout << "Nodes (i) " << a << " and (j) " << *its << " are mate" << endl;

					int b = *its;
					int stopper_m = 0;

					while (true)
					{
						stopper_m++;

						cout << "-------- Iter " << stopper_m << " --------" << endl;

						int random_mate = degree_list[irand(degree_list.size() - 1)];
						while (random_mate == a || random_mate == b)
							random_mate = degree_list[irand(degree_list.size() - 1)];

						cout << "Random another node k (not i nor j): " << random_mate << endl;

						if (!(they_are_mate(a, random_mate, member_list)) && (en[a].find(random_mate) == en[a].end()))
						{
							cout << "Node (k) " << random_mate << " is not mate and not connected with (i) " << a << endl;

							deque<int> not_common;
							for (set<int>::iterator it_est = en[random_mate].begin(); it_est != en[random_mate].end(); it_est++)
								if ((b != (*it_est)) && (en[b].find(*it_est) == en[b].end()))
									not_common.push_back(*it_est);

							cout << "Neighbors of (k) " << random_mate << " that are not (j) " << b << " or neighbors of (j): ";
							for (int i = 0; i < not_common.size(); i++)
								cout << not_common[i] << " ";
							cout << endl;

							if (not_common.size() > 0)
							{
								int node_h = not_common[irand(not_common.size() - 1)];

								cout << "Pick randomly a node h (neighbor of k that is not j or neighbors of j): " << node_h << endl;

								en[random_mate].erase(node_h);
								en[random_mate].insert(a);

								en[node_h].erase(random_mate);
								en[node_h].insert(b);

								en[b].erase(a);
								en[b].insert(node_h);

								en[a].insert(random_mate);
								en[a].erase(b);

								cout << "Remove link between (h) " << node_h << " and (k) " << random_mate << endl;
								cout << "Add link between (i) " << a << " and (k) " << random_mate << endl;
								cout << "Remove link between (i) " << a << " and (j) " << b << endl;
								cout << "Add link between (h) " << node_h << " and (j) " << b << endl;

								if (!they_are_mate(b, node_h, member_list)) {
									var_mate -= 2;
									cout << "Nodes (j) " << b << " and (h) " << node_h << " are not mate. So, number of mate nodes decreased by 2" << endl;
								}

								if (they_are_mate(random_mate, node_h, member_list)) {
									var_mate -= 2;
									cout << "Nodes (k) " << random_mate << " and (h) " << node_h << " are mate. So, number of mate nodes decreased by 2" << endl;
								}

								break;
							}
						}

						if (stopper_m == en[a].size()) {
							cout << "Break the loop" << endl;
							break;
						}
					}

					cout << "There was a change in edge list. Stop." << endl;
					break;
				}
			}
		}

		cout << "Check the number of mate nodes after rewiring" << endl;

		if (var_mate == best_var_mate)
		{
			cout << "There is a change in the number of mate nodes. Push the limit..." << endl;

			stopper_mate++;
			if (stopper_mate == mate_trooper) {
				cout << "Exceeded the maximum number of iterations" << endl;
				break;
			}
		}
		else {
			cout << "There is no change in the number of mate nodes. Reset limit..." << endl;

			stopper_mate = 0;
		}
	}

	cout << "--- End of process ---" << endl;

	for (int i = 0; i < en.size(); i++)
	{
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			if (i < *its)
			{
				E[i].insert(*its);
				E[*its].insert(i);
			}
	}

	cout << "External edge list after removing internal links" << endl;
	for (int i = 0; i < en.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = en[i].begin(); its != en[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	cout << "Edge list after connecting all the parts" << endl;
	for (int i = 0; i < E.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator its = E[i].begin(); its != E[i].end(); its++)
			cout << *its << " ";
		cout << endl;
	}

	return 0;
}

int internal_kin(deque<set<int>> &E, const deque<deque<int>> &member_list, int i)
{

	int var_mate2 = 0;
	for (set<int>::iterator itss = E[i].begin(); itss != E[i].end(); itss++)
		if (they_are_mate(i, *itss, member_list))
			var_mate2++;

	return var_mate2;
}

int internal_kin_only_one(set<int> &E, const deque<int> &member_matrix_j)
{ // return the overlap between E and member_matrix_j

	int var_mate2 = 0;

	for (set<int>::iterator itss = E.begin(); itss != E.end(); itss++)
	{

		if (binary_search(member_matrix_j.begin(), member_matrix_j.end(), *itss))
			var_mate2++;
	}

	return var_mate2;
}

int erase_links(
	deque<set<int>> &E, 
	const deque<deque<int>> &member_list, 
	const bool excess, const bool defect, 
	const double mixing_parameter)
{

	int num_nodes = member_list.size();

	int eras_add_times = 0;

	if (excess)
	{
		cout << "Excess parameter is set to true" << endl;

		for (int i = 0; i < num_nodes; i++)
		{

			while ((E[i].size() > 1) && double(internal_kin(E, member_list, i)) / E[i].size() < 1 - mixing_parameter)
			{

				//---------------------------------------------------------------------------------

				cout << "degree sequence changed to respect the option -sup ... " << ++eras_add_times << endl;

				deque<int> deqar;
				for (set<int>::iterator it_est = E[i].begin(); it_est != E[i].end(); it_est++)
					if (!they_are_mate(i, *it_est, member_list))
						deqar.push_back(*it_est);

				if (deqar.size() == E[i].size())
				{ // this shouldn't happen...

					cerr << "sorry, something went wrong: there is a node which does not respect the constraints. (option -sup)" << endl;
					return -1;
				}

				int random_mate = deqar[irand(deqar.size() - 1)];

				E[i].erase(random_mate);
				E[random_mate].erase(i);
			}
		}
	}

	if (defect)
	{
		cout << "Defect parameter is set to true" << endl;

		for (int i = 0; i < num_nodes; i++)
			while ((E[i].size() < E.size()) && double(internal_kin(E, member_list, i)) / E[i].size() > 1 - mixing_parameter)
			{

				//---------------------------------------------------------------------------------

				cout << "degree sequence changed to respect the option -inf ... " << ++eras_add_times << endl;

				int stopper_here = num_nodes;
				int stopper_ = 0;

				int random_mate = irand(num_nodes - 1);
				while (((they_are_mate(i, random_mate, member_list)) || E[i].find(random_mate) != E[i].end()) && (stopper_ < stopper_here))
				{

					random_mate = irand(num_nodes - 1);
					stopper_++;
				}

				if (stopper_ == stopper_here)
				{ // this shouldn't happen...

					cerr << "sorry, something went wrong: there is a node which does not respect the constraints. (option -inf)" << endl;
					return -1;
				}

				E[i].insert(random_mate);
				E[random_mate].insert(i);
			}
	}

	return 0;
}

int print_network(deque<set<int>> &E, const deque<deque<int>> &member_list, const deque<deque<int>> &member_matrix, deque<int> &num_seq)
{

	int edges = 0;

	int num_nodes = member_list.size();

	deque<double> double_mixing;
	for (int i = 0; i < E.size(); i++)
	{

		double one_minus_mu = double(internal_kin(E, member_list, i)) / E[i].size();

		double_mixing.push_back(1. - one_minus_mu);

		edges += E[i].size();
	}

	// cout<<"\n----------------------------------------------------------"<<endl;
	// cout<<endl;

	double density = 0;
	double sparsity = 0;

	for (int i = 0; i < member_matrix.size(); i++)
	{

		double media_int = 0;
		double media_est = 0;

		for (int j = 0; j < member_matrix[i].size(); j++)
		{

			double kinj = double(internal_kin_only_one(E[member_matrix[i][j]], member_matrix[i]));
			media_int += kinj;
			media_est += E[member_matrix[i][j]].size() - double(internal_kin_only_one(E[member_matrix[i][j]], member_matrix[i]));
		}

		double pair_num = (member_matrix[i].size() * (member_matrix[i].size() - 1));
		double pair_num_e = ((num_nodes - member_matrix[i].size()) * (member_matrix[i].size()));

		if (pair_num != 0)
			density += media_int / pair_num;
		if (pair_num_e != 0)
			sparsity += media_est / pair_num_e;
	}

	density = density / member_matrix.size();
	sparsity = sparsity / member_matrix.size();

	ofstream out1("network.dat");
	for (int u = 0; u < E.size(); u++)
	{

		set<int>::iterator itb = E[u].begin();

		while (itb != E[u].end())
			out1 << u + 1 << "\t" << *(itb++) + 1 << endl;
	}

	ofstream out2("community.dat");

	for (int i = 0; i < member_list.size(); i++)
	{

		out2 << i + 1 << "\t";
		for (int j = 0; j < member_list[i].size(); j++)
			out2 << member_list[i][j] + 1 << " ";
		out2 << endl;
	}

	cout << "\n\n---------------------------------------------------------------------------" << endl;

	cout << "network of " << num_nodes << " vertices and " << edges / 2 << " edges"
		 << ";\t average degree = " << double(edges) / num_nodes << endl;
	cout << "\naverage mixing parameter: " << average_func(double_mixing) << " +/- " << sqrt(variance_func(double_mixing)) << endl;
	cout << "p_in: " << density << "\tp_out: " << sparsity << endl;

	ofstream statout("statistics.dat");

	deque<int> degree_seq;
	for (int i = 0; i < E.size(); i++)
		degree_seq.push_back(E[i].size());

	statout << "degree distribution (probability density function of the degree in logarithmic bins) " << endl;
	log_histogram(degree_seq, statout, 10);
	statout << "\ndegree distribution (degree-occurrences) " << endl;
	int_histogram(degree_seq, statout);
	statout << endl
			<< "--------------------------------------" << endl;

	statout << "community distribution (size-occurrences)" << endl;
	int_histogram(num_seq, statout);
	statout << endl
			<< "--------------------------------------" << endl;

	statout << "mixing parameter" << endl;
	not_norm_histogram(double_mixing, statout, 20, 0, 0);
	statout << endl
			<< "--------------------------------------" << endl;

	cout << endl
		 << endl;

	return 0;
}

int benchmark(
	bool excess, bool defect,
	int num_nodes,
	double average_k, int max_degree,
	double tau, double tau2,
	double mixing_parameter,
	int overlapping_nodes, int overlap_membership,
	int nmin, int nmax, bool fixed_range,
	double ca)
{
	cout << "-----------------------------------------------------------" << endl;

	cout << "Excess: " << excess << endl;
	cout << "Defect: " << defect << endl
		 << endl;

	cout << "Number of nodes: " << num_nodes << endl
		 << endl;

	cout << "Average degree: " << average_k << endl;
	cout << "Maximum degree: " << max_degree << endl;
	cout << "Tau: " << tau << endl
		 << endl;

	cout << "Fixed range for community size: " << fixed_range << endl;
	cout << "Minimum community size: " << nmin << endl;
	cout << "Maximum community size: " << nmax << endl;
	cout << "Tau2: " << tau2 << endl
		 << endl;

	cout << "Mixing parameter: " << mixing_parameter << endl;

	cout << "-----------------------------------------------------------" << endl;

	// Solve for minimum degree
	double dmin = solve_dmin(max_degree, average_k, -tau);
	if (dmin == -1)
		return -1;
	int min_degree = int(dmin);
	cout << "Minimum degree (float): " << dmin << ", (int): " << min_degree << endl;

	double media1 = integer_average(max_degree, min_degree, tau);
	double media2 = integer_average(max_degree, min_degree + 1, tau);
	if (fabs(media1 - average_k) > fabs(media2 - average_k))
		min_degree++;
	cout << "Average if min_degree is " << min_degree << ": " << media1 << ", difference: " << fabs(media1 - average_k) << endl;
	cout << "Average if min_degree is " << min_degree + 1 << ": " << media2 << ", difference: " << fabs(media2 - average_k) << endl;
	cout << "Minimum degree (int, adjusted): " << min_degree << endl;

	cout << "-----------------------------------------------------------" << endl;

	if (!fixed_range)
	{
		cout << "Fixed range: false" << endl;

		nmax = max_degree;
		nmin = max(int(min_degree), 3);
	}
	else
	{
		cout << "Fixed range: true" << endl;
	}
	cout << "Community size range = [" << nmin << " , " << nmax << "]" << endl;

	cout << "-----------------------------------------------------------" << endl;

	deque<double> cumulative;
	powerlaw(max_degree, min_degree, tau, cumulative);

	cout << "Cumulative distribution for the degree sequence:" << endl;
	for (int i = 0; i < cumulative.size(); i++)
	{
		cout << cumulative[i] << " ";
	}
	cout << endl;

	deque<int> degree_seq;
	for (int i = 0; i < num_nodes; i++)
	{
		int nn = lower_bound(cumulative.begin(), cumulative.end(), ran4()) - cumulative.begin() + min_degree;
		degree_seq.push_back(nn);
	}

	cout << "Degree sequence (raw):" << endl;
	for (int i = 0; i < degree_seq.size(); i++)
	{
		cout << degree_seq[i] << " ";
	}
	cout << endl;

	sort(degree_seq.begin(), degree_seq.end());

	cout << "Degree sequence (sorted):" << endl;
	for (int i = 0; i < degree_seq.size(); i++)
	{
		cout << degree_seq[i] << " ";
	}
	cout << endl;

	if (deque_int_sum(degree_seq) % 2 != 0)
	{
		cout << "Sum of the degree sequence is " << deque_int_sum(degree_seq) << ", which is odd. Adjusting..." << endl;
		degree_seq[max_element(degree_seq.begin(), degree_seq.end()) - degree_seq.begin()]--;
	}

	cout << "Degree sequence (sorted, even sum):" << endl;
	for (int i = 0; i < degree_seq.size(); i++)
	{
		cout << degree_seq[i] << " ";
	}
	cout << endl;

	cout << "-----------------------------------------------------------" << endl;

	deque<deque<int>> member_matrix;
	deque<int> num_seq;
	deque<int> internal_degree_seq;

	if (internal_degree_and_membership(
			mixing_parameter,
			overlapping_nodes, overlap_membership,
			num_nodes,
			member_matrix,
			excess, defect,
			degree_seq, num_seq, internal_degree_seq,
			fixed_range, nmin, nmax, tau2) == -1)
		return -1;

	cout << "Community size sequence:" << endl;
	for (int i = 0; i < num_seq.size(); i++)
	{
		cout << num_seq[i] << " ";
	}
	cout << endl;

	cout << "Membership matrix: " << endl;
	for (int i = 0; i < member_matrix.size(); i++)
	{
		cout << i << " (" << member_matrix[i].size() << "): ";
		for (int j = 0; j < member_matrix[i].size(); j++)
		{
			cout << member_matrix[i][j] << " ";
		}
		cout << endl;
	}

	cout << "Internal degree sequence:" << endl;
	for (int i = 0; i < internal_degree_seq.size(); i++)
	{
		cout << i << " (" << internal_degree_seq[i] << ") ";
	}
	cout << endl;

	cout << "-----------------------------------------------------------" << endl;

	cout << "Building subgraphs..." << endl;

	deque<set<int>> E;
	deque<deque<int>> member_list;
	deque<deque<int>> link_list;

	if (build_subgraphs(E, member_matrix, member_list, link_list, internal_degree_seq, degree_seq, excess, defect) == -1)
		return -1;

	// cout << "Edge list:" << endl;
	// for (int i = 0; i < E.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (set<int>::iterator it = E[i].begin(); it != E[i].end(); it++)
	// 	{
	// 		cout << *it << " ";
	// 	}
	// 	cout << endl;
	// }

	// cout << "Membership list:" << endl;
	// for (int i = 0; i < member_list.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (int j = 0; j < member_list[i].size(); j++)
	// 	{
	// 		cout << member_list[i][j] << " ";
	// 	}
	// 	cout << endl;
	// }

	// cout << "Link list:" << endl;
	// for (int i = 0; i < link_list.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (int j = 0; j < link_list[i].size(); j++)
	// 	{
	// 		cout << link_list[i][j] << " ";
	// 	}
	// 	cout << endl;
	// }

	cout << "-----------------------------------------------------------" << endl;

	cout << "Connecting all the parts..." << endl;

	connect_all_the_parts(E, member_list, link_list);

	// cout << "Edge list:" << endl;
	// for (int i = 0; i < E.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (set<int>::iterator it = E[i].begin(); it != E[i].end(); it++)
	// 	{
	// 		cout << *it << " ";
	// 	}
	// 	cout << endl;
	// }

	// cout << "Membership list:" << endl;
	// for (int i = 0; i < member_list.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (int j = 0; j < member_list[i].size(); j++)
	// 	{
	// 		cout << member_list[i][j] << " ";
	// 	}
	// 	cout << endl;
	// }

	// cout << "Link list:" << endl;
	// for (int i = 0; i < link_list.size(); i++)
	// {
	// 	cout << i << ": ";
	// 	for (int j = 0; j < link_list[i].size(); j++)
	// 	{
	// 		cout << link_list[i][j] << " ";
	// 	}
	// 	cout << endl;
	// }

	cout << "-----------------------------------------------------------" << endl;

	cout << "Erasing links..." << endl;

	if (erase_links(E, member_list, excess, defect, mixing_parameter) == -1)
		return -1;

	cout << "Edge list:" << endl;
	for (int i = 0; i < E.size(); i++)
	{
		cout << i << ": ";
		for (set<int>::iterator it = E[i].begin(); it != E[i].end(); it++)
		{
			cout << *it << " ";
		}
		cout << endl;
	}

	cout << "-----------------------------------------------------------" << endl;

	if (ca != unlikely)
	{
		cout << "The clustering coefficient is set to " << ca << ", the network will be rewired to respect it." << endl;
		cclu(E, member_list, member_matrix, ca);

		cout << "Edge list:" << endl;
		for (int i = 0; i < E.size(); i++)
		{
			cout << i << ": ";
			for (set<int>::iterator it = E[i].begin(); it != E[i].end(); it++)
			{
				cout << *it << " ";
			}
			cout << endl;
		}

		cout << "Membership list:" << endl;
		for (int i = 0; i < member_list.size(); i++)
		{
			cout << i << ": ";
			for (int j = 0; j < member_list[i].size(); j++)
			{
				cout << member_list[i][j] << " ";
			}
			cout << endl;
		}

		cout << "Membership matrix:" << endl;
		for (int i = 0; i < member_matrix.size(); i++)
		{
			cout << i << ": ";
			for (int j = 0; j < member_matrix[i].size(); j++)
			{
				cout << member_matrix[i][j] << " ";
			}
			cout << endl;
		}
	}
	else
	{
		cout << "The clustering coefficient is set to " << ca << ", the network will not be rewired." << endl;
	}

	cout << "-----------------------------------------------------------" << endl;

	cout << "Printing network..." << endl;
	print_network(E, member_list, member_matrix, num_seq);

	return 0;
}

void erase_file_if_exists(string s)
{

	char b[100];
	cast_string_to_char(s, b);

	ifstream in1(b);

	if (in1.is_open())
	{

		char rmb[120];
		sprintf(rmb, "rm %s", b);

		int erase = system(rmb);
	}
}

int main(int argc, char *argv[])
{
	srand_file();
	Parameters p;

	if (set_parameters(argc, argv, p) == false)
	{
		if (argc > 1)
			cerr << "Please, look at ReadMe.txt..." << endl;
		return -1;
	}

	erase_file_if_exists("network.dat");
	erase_file_if_exists("community.dat");
	erase_file_if_exists("statistics.dat");

	benchmark(
		p.excess, p.defect,
		p.num_nodes,
		p.average_k, p.max_degree,
		p.tau, p.tau2,
		p.mixing_parameter,
		p.overlapping_nodes, p.overlap_membership,
		p.nmin, p.nmax, p.fixed_range,
		p.clustering_coeff);

	return 0;
}
