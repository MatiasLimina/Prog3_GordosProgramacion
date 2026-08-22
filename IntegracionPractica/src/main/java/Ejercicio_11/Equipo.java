package Ejercicio_11;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Equipo {
    private String nombreEquipo;
    private Lider lider;
    private List<Vendedor> vendedores; // Agregación / Composición 1 — 1..*

    public Equipo(String nombreEquipo) {
        Objects.requireNonNull(nombreEquipo, "El nombre del equipo no puede ser nulo");
        this.nombreEquipo = nombreEquipo;
        this.vendedores = new ArrayList<>();
    }

    public void agregarVendedor(Vendedor vendedor) {
        Objects.requireNonNull(vendedor, "El vendedor no puede ser nulo");
        if (!vendedores.contains(vendedor)) {
            vendedores.add(vendedor);
        }
    }

    public String getNombreEquipo() {
        return nombreEquipo;
    }

    public void setNombreEquipo(String nombreEquipo) {
        Objects.requireNonNull(nombreEquipo, "El nombre del equipo no puede ser nulo");
        this.nombreEquipo = nombreEquipo;
    }

    public Lider getLider() {
        return lider;
    }

    public void setLider(Lider lider) {
        Objects.requireNonNull(lider, "El líder no puede ser nulo");
        this.lider = lider;
    }

    public List<Vendedor> getVendedores() {
        return Collections.unmodifiableList(vendedores);
    }
}
