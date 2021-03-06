import psi4
import numpy as np

from scf import SCF


class UHF(SCF):
    """
    Unrestricted Hartree-Fock class
    """
    def __init__(self, options_ini):
        super().__init__(options_ini)
        self.n_occ_a = int(self.config['DEFAULT']['nalpha'])
        self.n_occ_b = int(self.config['DEFAULT']['nbeta'])
        
    def energy(self):
        """
        Compute the UHF energy
        """
        energies = [0.0]
        densities = [np.zeros_like(self.H)]
        d_norms = []

        g, H, A, n_occ_a, n_occ_b, V_nuc = self.g, self.H, self.A, self.n_occ_a, self.n_occ_b, self.V_nuc

        # Core guess
        Fa, Fb = H, H

        print('Iter         Energy            ΔE         ‖ΔD‖')
        print('--------------------------------------------------')
        for iteration in range(self.options['SCF_MAX_ITER']):
            # Transform Fock matrices
            tFa = A @ Fa @ A
            tFb = A @ Fb @ A

            # Diagonalize Fock matrices
            ea, tCa = np.linalg.eigh(tFa)
            eb, tCb = np.linalg.eigh(tFb)

            # Construct new SCF eigenvectors
            Ca = A @ tCa
            Cb = A @ tCb
            Cocc_a = Ca[:, :n_occ_a]
            Cocc_b = Cb[:, :n_occ_b]

            # Form new density
            Da = Cocc_a @ Cocc_a.T
            Db = Cocc_b @ Cocc_b.T
            DT = Da + Db
            densities.append(DT)

            # Construct Fock
            Ja = np.einsum('pqrs,rs->pq', g, Da)
            Jb = np.einsum('pqrs,rs->pq', g, Db)
            Ka = np.einsum('prqs,rs->pq', g, Da)
            Kb = np.einsum('prqs,rs->pq', g, Db)
            Fa = H + Ja - Ka + Jb
            Fb = H + Jb - Kb + Ja

            #E_scf = np.einsum('pq,pq->', (H + Fa)/2, Da) + np.einsum('pq,pq->', (H + Fb)/2, Db) + self.molecule.nuclear_repulsion_energy()
            E_scf = np.trace((H + Fa) @ Da + (H + Fb) @ Db)/2 + V_nuc

            energies.append(E_scf)
            ΔE = energies[-1] - energies[-2]
            d_norms.append(np.linalg.norm(densities[-2] - densities[-1]))
            print('{:3d} {:> 20.14f} {:> 1.5E}  {:>1.5E}'.format(iteration, E_scf, ΔE, d_norms[-1]))

            if abs(ΔE) < 1.0e-10 and d_norms[-1] < 1.0e-10:
                break

        print('\nUHF Energy: {:> 15.10f}'.format(E_scf))
        self.energies, self.densities, self.d_norms = energies, densities, d_norms
        self.Ca, self.Cb, self.ea, self.eb, self.E_scf = Ca, Cb, ea, eb, E_scf

        return E_scf


if __name__ == "__main__":
    water = UHF('Options.ini')
    water.energy()
    water.plot_convergence()
    #water.plot_density_changes()
