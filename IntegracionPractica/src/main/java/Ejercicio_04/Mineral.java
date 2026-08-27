package Ejercicio_04;

import java.util.ArrayList;
import java.util.List;

public class Mineral {
    private String nombre;
    private boolean esPrimario; // true = primario, false = secundario

    public Mineral(String nombre, boolean esPrimario) {
        this.nombre = nombre;
        this.esPrimario = esPrimario;
    }

    public boolean esPrimario() {
        return esPrimario;
    }

    public String getNombre() { return nombre; }
}
