package Ejercicio_08;

import java.util.ArrayList;
import java.util.List;

public class Propietario extends Persona {
    private List<Avion> avionesAdquiridos;

    public Propietario(String nss, String nombre, String direccion, String telefono) {
        super(nss, nombre, direccion, telefono);
        this.avionesAdquiridos = new ArrayList<>();
    }

    public void comprarAvion(Avion a) {
        if (!avionesAdquiridos.contains(a)) {
            avionesAdquiridos.add(a);
        }
    }

    public List<Avion> getAvionesAdquiridos() { return avionesAdquiridos; }
}
